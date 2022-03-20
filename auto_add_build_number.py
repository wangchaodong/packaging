#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tools as tools
import configs as constant_configs
    
    
if __name__ == '__main__':
    constant_configs.prepare_config()
    tools.add_build_number(project_pbxproj_path=constant_configs.get_xcode_project_pbxproj_path(),
                           target_name=constant_configs.get_target_name(),
                           project_pbxproj_dir=constant_configs.get_xcode_project_path())
