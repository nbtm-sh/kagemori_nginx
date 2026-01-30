from setuptools import setup, find_packages

requirements = [ 'chibi-nginx==1.0.0', 'psutil' ]

setup(
    author="nbtm-sh",
    author_email="n.glades@unsw.edu.au",
    description="nginx configuration wrapper for kagemori",
    install_requires=requirements,
    packages=find_packages(include=['kagemori_nginx']),
    version="0.1rc3",
    name="kagemori-nginx"
)
