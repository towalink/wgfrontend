import os
import setuptools


with open('README.md', 'r') as f:
    long_description = f.read()

setup_kwargs = {
    'name': 'wgfrontend',
    'version': '0.2.0',
    'author': 'The Towalink Project',
    'author_email': 'pypi.wgfrontend@towalink.net',
    'description': 'web-based user interface for configuring WireGuard for roadwarriors',
    'long_description': long_description,
    'long_description_content_type': 'text/markdown',
    'url': 'https://www.github.com/towalink/wgfrontend',
    'packages': setuptools.find_packages('src'),
    'package_dir': {'': 'src'},
    'include_package_data': True,
    'install_requires': ['cherrypy',
                         'jinja2',
                         'qrcode',
                         'wgconfig'
                        ],
    'entry_points': '''
        [console_scripts]
        wgfrontend=wgfrontend:main
        wgfrontend-password=pwdtools:hash_password_interactively
    ''',
    'classifiers': [
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Development Status :: 3 - Alpha',
        #'Development Status :: 4 - Beta',
        #'Development Status :: 5 - Production/Stable',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Telecommunications Industry',
        'Topic :: System :: Networking'
    ],
    'python_requires': '>=3.6',
    'keywords': 'Towalink VPN webfrontend WireGuard',
    'project_urls': {
        'Project homepage': 'https://www.towalink.net',
        'Repository': 'https://www.github.com/towalink/wgfrontend',
        'Documentation': 'https://towalink.readthedocs.io',
    },
}


if __name__ == '__main__':
    setuptools.setup(**setup_kwargs)
