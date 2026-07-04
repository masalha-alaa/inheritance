import argparse
from importlib import import_module

from settings import FIQH_ENGINE, SUPPORTED_FIQH_ENGINES


def _build_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--fiqh-engine", choices=SUPPORTED_FIQH_ENGINES)
    return parser


def validate_fiqh_engine_name(engine_name):
    if engine_name not in SUPPORTED_FIQH_ENGINES:
        choices = ", ".join(SUPPORTED_FIQH_ENGINES)
        raise ValueError(f"Unsupported Fiqh engine {engine_name!r}. Expected one of: {choices}")
    return engine_name


def resolve_fiqh_engine_name(argv=None):
    args, _ = _build_parser().parse_known_args(argv)
    return validate_fiqh_engine_name(args.fiqh_engine or FIQH_ENGINE)


def create_fiqh(engine_name=None):
    resolved_engine_name = validate_fiqh_engine_name(engine_name) if engine_name else resolve_fiqh_engine_name()
    fiqh_module = import_module(resolved_engine_name)
    fiqh = fiqh_module.Fiqh()
    fiqh.initialize()
    return fiqh
