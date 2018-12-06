import tempfile
import os
import shutil
import re

from conans import ConanFile, CMake, tools
from conans.errors import ConanException


repo_name = "aws-lambda-cpp"
aws_lambda_cpp_git = "https://github.com/awslabs/{}.git".format(repo_name)
branch = "master"


def get_version():
    tmp_folder = tempfile.mkdtemp()
    try:
        git = tools.Git(folder=tmp_folder)
        git.clone(url=aws_lambda_cpp_git, branch=branch)
        with open(os.path.join(tmp_folder, "CMakeLists.txt"), "r") as f:
            first_lines = ''.join([it.strip() for it in f.readlines()[:10]])
            m = re.match(r".*project\(aws-lambda-runtime[\s\n\r]*VERSION\s*(?P<version>[0-9.]+)[\s\n\r]*[^)]*\).*", first_lines)
            return m.group("version")
    except:
        shutil.rmtree(tmp_folder)
        raise ConanException("Cannot get version from Github repository")


class AWSLambdaRuntimeConan(ConanFile):
    name = "aws-lambda-runtime"
    version = get_version()

    license = "<Put the package license here>"
    author = "<Put your name here> <And your email here>"
    url = "<Package recipe repository url here, for issues about the package>"
    description = "<Description of Awslambdacpp here>"
    topics = ("<Put some tag here>", "<here>", "<and here>")

    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    generators = "cmake"

    def requirements(self):
        self.requires("libcurl/7.56.1@bincrafters/stable")

    def source(self):
        self.run("git clone {}".format(aws_lambda_cpp_git))
        self.run("cd {} && git checkout {}".format(repo_name, branch))
        # This small hack might be useful to guarantee proper /MT /MD linkage
        # in MSVC if the packaged project doesn't have variables to set it
        # properly
        tools.replace_in_file(os.path.join(repo_name, "CMakeLists.txt"),
                              'option(ENABLE_TESTS "Enables building the test project, requires AWS C++ SDK." OFF)',
                              '''include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()
option(ENABLE_TESTS "Enables building the test project, requires AWS C++ SDK." OFF)
''')

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions['ENABLE_TESTS'] = False
        cmake.configure(source_dir=repo_name)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["aws-lambda-runtime"]

