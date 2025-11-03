"""Video source drivers package."""
from .PornhubDriver import PornhubDriver
from .XvideosDriver import XvideosDriver
from .XnxxDriver import XnxxDriver
from .SpankBangDriver import SpankBangDriver
from .RedtubeDriver import RedtubeDriver

__all__ = [
    'PornhubDriver',
    'XvideosDriver',
    'XnxxDriver',
    'SpankBangDriver',
    'RedtubeDriver',
]

# Registry of all available drivers
DRIVER_REGISTRY = {
    'pornhub': PornhubDriver,
    'xvideos': XvideosDriver,
    'xnxx': XnxxDriver,
    'spankbang': SpankBangDriver,
    'redtube': RedtubeDriver,
}


def get_driver(name: str):
    """Get a driver instance by name."""
    driver_class = DRIVER_REGISTRY.get(name.lower())
    if driver_class:
        return driver_class()
    return None


def get_all_drivers():
    """Get instances of all available drivers."""
    return [driver_class() for driver_class in DRIVER_REGISTRY.values()]
