import functools
import os

import click
from langchain.callbacks import get_openai_callback

from src.apis.jina_cloud import jina_auth_login
from src.options.configure.key_handling import set_api_key


def exception_interceptor(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise type(e)(f'''
{str(e)}

😱😱😱 Sorry for this experience. 
Could you please report an issue about this on our github repo? We'll try to fix it asap.
https://github.com/jina-ai/gptdeploy/issues/new
''') from e
    return wrapper

def path_param(func):
    @click.option('--path', required=True, help='Path to the generated microservice.')
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        path = os.path.expanduser(kwargs['path'])
        path = os.path.abspath(path)
        kwargs['path'] = path
        return func(*args, **kwargs)
    return wrapper


@click.group(invoke_without_command=True)
@click.pass_context
@exception_interceptor
def main(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.option('--description', required=True, help='Description of the microservice.')
@click.option('--test', required=True, help='Test scenario for the microservice.')
@click.option('--model', default='gpt-4', help='GPT model to use (default: gpt-4).')
@click.option('--verbose', default=False, is_flag=True, help='Verbose mode.')
@path_param
def generate(
        description,
        test,
        model,
        verbose,
        path,
):
    os.environ['VERBOSE'] = str(verbose)
    path = os.path.expanduser(path)
    path = os.path.abspath(path)
    if os.path.exists(path):
        if os.listdir(path):
            click.echo(f"Error: The path {path} you provided via --path is not empty. Please choose a directory that does not exist or is empty.")
            return

    from src.options.generate.generator import Generator
    generator = Generator(description, test, model=model)
    with get_openai_callback() as cb:
        generator.generate(path)
        print(f"Prompt/Completion/Total Tokens: {cb.prompt_tokens}/{cb.completion_tokens}/{cb.total_tokens}")
        print(f"Total Cost on OpenAI (USD): ${cb.total_cost}")

@main.command()
@path_param
def run(path):
    from src.options.run import Runner
    path = os.path.expanduser(path)
    path = os.path.abspath(path)
    Runner().run(path)


@main.command()
@path_param
def deploy(path):
    jina_auth_login()
    from src.options.deploy.deployer import Deployer
    path = os.path.expanduser(path)
    path = os.path.abspath(path)
    Deployer().deploy(path)

@main.command()
@click.option('--key', required=True, help='Your OpenAI API key.')
def configure(key):
    set_api_key(key)


if __name__ == '__main__':
    main()
