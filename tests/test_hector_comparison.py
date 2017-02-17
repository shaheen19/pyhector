# -*- coding: utf-8 -*-

import os
import subprocess

import pandas as pd
import pytest

import pyhector
from pyhector import (
    Hector, rcp26, rcp45, rcp60, rcp85, read_hector_input, read_hector_output
)


path = os.path.dirname(__file__)
rcps = {
    'rcp26': rcp26,
    'rcp45': rcp45,
    'rcp60': rcp60,
    'rcp85': rcp85
}

path = os.path.dirname(os.path.realpath(__file__))
hector_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "hector")
output_path = os.path.join(hector_path, "output")


@pytest.fixture
def compile_hector():
    if not os.path.exists(hector_path):
        p = subprocess.Popen(
            ["git", "clone", "https://github.com/JGCRI/hector.git",
             "--depth", "1"], cwd=path)
        p.wait()

    ver=["awk", "/define.*BOOST_LIB_VERSION/ {print $3}",
         "/usr/include/boost/version.hpp"]
    p = subprocess.run(ver, stdout=subprocess.PIPE)
    version = p.stdout.decode()
    p = subprocess.Popen(["git", "pull"], cwd=hector_path)
    p.wait()
    env = {
        **os.environ,
        "BOOSTLIB": "/usr/local/lib",
        "BOOSTVERSION": version,
        "BOOSTROOT": "/usr/include/boost"
    }
    p = subprocess.Popen(["make", "hector"], cwd=hector_path, env=env)
    p.wait()


@pytest.fixture
def run_rcps(compile_hector):
    for rcp in rcps.keys():
        output_stream = os.path.join(hector_path,
                          "output/outputstream_{}.csv".format(rcp))
        if os.path.exists(output_stream):
            os.remove(output_stream)
        ret = subprocess.call([
            "source/hector",
            "input/hector_{}.ini".format(rcp)
        ], cwd=hector_path)
        assert ret == 0
        assert os.path.exists(output_stream)


def test_hector_binary_exists(compile_hector):
    assert os.path.exists(os.path.join(hector_path, "source/hector"))


def test_rcps(run_rcps):
    # Compare output of Pyhector with Hector's output streams for RCPs.
    for name, scenario in rcps.items():
        original = read_hector_output(
            os.path.join(hector_path,
                         "./output/outputstream_{}.csv".format(name))
        )
        output, _ = pyhector.run(scenario)
        assert output["temperature.Tgav"].round(2).equals(
            original.Tgav.round(2))