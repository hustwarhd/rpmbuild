#!/usr/bin/python

# This script is used to generate rpm package from github

import sys
import os
import string
import time
from optparse import OptionParser

WorkDir = os.getcwd();

defaultSdkVersion = '1.1.77';
sdkVersion = defaultSdkVersion;

Spec = "Name:   vulkan-loader \n\
Version:    " + defaultSdkVersion + "\n\
Release:        0  \n\
Summary:        vulkan-loader \n\
\n\
Group:          System Environment/Daemons \n\
License:    Apache 2.0  \n\
URL:            https://vulkan.lunarg.com/ \n\
\n\
%description \n\
\n\
%files \n\
%doc \n\
/usr/lib64/libvulkan.so \n\
/usr/lib64/libvulkan.so.1 \n\
/usr/lib64/libvulkan.so." + defaultSdkVersion + " \n\
/usr/lib/libvulkan.so \n\
/usr/lib/libvulkan.so.1 \n\
/usr/lib/libvulkan.so." + defaultSdkVersion + " \n\
\n\
\n\
%changelog \n\
";

def GetOpt():
    global sdkVersion;
    global WorkDir;

    parser = OptionParser()

    parser.add_option("-t", "--targetSDK", action="store",
                  type="string",
                  dest="sdkVersion",
                  help="the target sdk version")

    (options, args) = parser.parse_args()

    if options.sdkVersion:
        print("The building loader version: %s" % (options.sdkVersion));
        sdkVersion = options.sdkVersion;
    else:
        print("The sdkVersion is not specified, default: " + sdkVersion);

def InstallDependency():
    os.system('yum install -y wget');
    os.system('wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm');
    os.system('yum localinstall -y epel-release-latest-7.noarch.rpm && yum update -y && yum install -y python34 libXrandr-devel libXrandr-devel.i686 gcc-c++ cmake python34 curl glibc-devel glibc-devel.i686 libstdc++-devel libstdc++-devel.i686 libxcb-devel libxcb-devel.i686 libX11-devel libX11-devel.i686 libxshmfence-devel libxshmfence-devel.i686 git make rpm-build rpm-devel rpmdevtools');
    os.system('git config --global user.email \"jacob.he@amd.com\"');
    os.system('git config --global user.name \"Jacob He\"');
    os.system('git config --global color.ui false');

def DownloadRPMBuild():
    global sdkVersion;
    global WorkDir;

    os.chdir(WorkDir);
    if not os.path.exists("rpmbuild"):
        print("Downloading rpmbuild.....");
        if os.system('git clone https://github.com/hustwarhd/rpmbuild.git -b master'):
            print('Download rpmbuild failed');
            exit(-1);
    else:
        os.system('git checkout master');
        os.system('git pull');

    spec_file = open(WorkDir + "/rpmbuild/SPECS/vulkan-loader.spec",'w');
    print >> spec_file,Spec.replace(defaultSdkVersion, sdkVersion);
    spec_file.close()

def DownloadAndCompileLoader():
    global sdkVersion;
    global WorkDir;
    os.chdir(WorkDir);

    if not os.path.exists("Vulkan-Loader"):
    	if os.system('git clone https://github.com/KhronosGroup/Vulkan-Loader.git -b sdk-' + sdkVersion):
        	print('Download Vulkan-Loader failed');
        	exit(-1);
    else:
    	os.chdir(WorkDir + '/Vulkan-Loader');
    	os.system('git pull')
    	if os.system('git checkout remotes/origin/sdk-' + sdkVersion + ' -b sdk-' + sdkVersion):
            os.system('git checkout -b sdk-' + sdkVersion);

    if not os.path.exists("Vulkan-Headers"):
    	if os.system('git clone https://github.com/KhronosGroup/Vulkan-Headers -b sdk-' + sdkVersion):
            print('Download Vulkan-Headers failed');
            exit(-1);
    else:
    	os.chdir(WorkDir + '/Vulkan-Headers');
    	os.system('git pull')
    	if os.system('git checkout remotes/origin/sdk-' + sdkVersion + ' -b sdk-' + sdkVersion):
            os.system('git checkout -b sdk-' + sdkVersion);

    os.chdir(WorkDir + '/Vulkan-Headers');
    if os.path.exists("build"):
	os.system('rm build -rf');

    if os.system('mkdir build && cd build && cmake .. && make && make install'):
        print('Build Vulkan-Headers failed');
        exit(-1);
        
    os.chdir(WorkDir + '/Vulkan-Loader');

    if not os.path.exists("external/googletest"):
        if os.system('git clone https://github.com/google/googletest external/googletest'):
            print('Download googletest failed');
            exit(-1);
    else:
    	os.chdir(WorkDir + '/Vulkan-Loader/external/googletest');
    	os.system('git pull')
  
    os.chdir(WorkDir + '/Vulkan-Loader');
    if os.path.exists("release64"):
	os.system('rm release64 -rf');
    if os.system('cmake -H. -Brelease64 -DCMAKE_BUILD_TYPE=Release -DBUILD_WSI_WAYLAND_SUPPORT=OFF -DVULKAN_HEADERS_INSTALL_DIR=' + WorkDir +'/Vulkan-Headers/build/install'):
        print('cmake Vulkan-Loader failed');
        exit(-1);

    os.chdir(WorkDir + '/Vulkan-Loader/release64');
    if os.system('make -j8'):
        print('Build Vulkan-Loader failed');
        exit(-1);
        
    os.chdir(WorkDir + '/Vulkan-Loader');
    if os.path.exists("release"):
	os.system('rm release -rf');
    if os.system('export ASFLAGS=--32 && export CFLAGS=-m32 && export CXXFLAGS=-m32 && export PKG_CONFIG_LIBDIR=/usr/lib/i386-linux-gnu && cmake -H. -Brelease -DCMAKE_BUILD_TYPE=Release -DBUILD_WSI_WAYLAND_SUPPORT=OFF -DVULKAN_HEADERS_INSTALL_DIR=' + WorkDir + '/Vulkan-Headers/build/install'):
        print('cmake 32bit Vulkan-Loader failed');
        exit(-1);
    os.chdir(WorkDir + '/Vulkan-Loader/release');
    if os.system('make -j8'):
        print('Build 32bit Vulkan-Loader failed');
        exit(-1);

def Package():
    global sdkVersion;
    global WorkDir;

    LibName = 'libvulkan.so.' + sdkVersion; 
    BuildRoot = WorkDir + '/rpmbuild/BUILDROOT/vulkan-loader-' + sdkVersion + '-0.x86_64/usr';
    os.chdir(WorkDir);

    os.system('rm -rf rpmbuild/BUILDROOT/*');
    os.system('mkdir -p ' + BuildRoot + '/lib64');
    os.system('mkdir -p ' + BuildRoot + '/lib');
    os.system('cp ' + WorkDir + '/Vulkan-Loader/release64/loader/' + LibName + ' ' + BuildRoot + '/lib64');
    os.system('cp ' + WorkDir + '/Vulkan-Loader/release/loader/' + LibName + ' ' + BuildRoot + '/lib');
    os.chdir(BuildRoot + '/lib64');
    os.system('ln -s ' + LibName + ' libvulkan.so.1');
    os.system('ln -s libvulkan.so.1 libvulkan.so');
    os.chdir(BuildRoot + '/lib');
    os.system('ln -s ' + LibName + ' libvulkan.so.1');
    os.system('ln -s libvulkan.so.1 libvulkan.so');
    os.system('cp -a ' + WorkDir + '/rpmbuild ' + '~/');
    os.chdir('/root/rpmbuild/SPECS');
    os.system('rpmbuild -ba vulkan-loader.spec');
    os.system('cp /root/rpmbuild/RPMS/x86_64/*.rpm ' + WorkDir);

# main
GetOpt();
InstallDependency();
DownloadRPMBuild();
DownloadAndCompileLoader();
Package();

