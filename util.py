# Copyright 2024 Tachi
# THIS FILE HAS BEEN MODIFIED FROM THE ORIGINAL
# Including refactors and bugfixes to support Blender 4.2+
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

def logger(submodule=None):
    return logging.getLogger("nodes_graphviz_arrange" +
                             ("." + submodule if submodule is not None else ""))


def write_line(line, f):
    logger("gv_input").debug(line)
    print(line, file=f)