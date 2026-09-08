cmake_minimum_required(VERSION 3.10 FATAL_ERROR)

project(BeHappyBotApi VERSION 10.3 LANGUAGES CXX)

add_subdirectory(bhlib EXCLUDE_FROM_ALL)

if (NOT DEFINED CMAKE_MODULE_PATH)
  set(CMAKE_MODULE_PATH "")
endif()
set(CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/bhlib/CMake" "${CMAKE_MODULE_PATH}")

if (NOT DEFINED CMAKE_INSTALL_BINDIR)
  set(CMAKE_INSTALL_BINDIR "bin")
endif()

if (POLICY CMP0074)
  # use environment variables to find libraries
  cmake_policy(SET CMP0074 NEW)
endif()

include(PreventInSourceBuild)
prevent_in_source_build()

if (BEHAPPY_BOT_API_ENABLE_LTO)
  include(CheckIPOSupported)
  check_ipo_supported(RESULT IPO_SUPPORTED LANGUAGES CXX)
  if (IPO_SUPPORTED)
    string(REPLACE ";" " " CXX_FLAGS_IPO "${CMAKE_CXX_COMPILE_OPTIONS_IPO}")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${CXX_FLAGS_IPO}")

    string(REPLACE ";" " " LINK_FLAGS_IPO "${CMAKE_CXX_LINK_OPTIONS_IPO}")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${LINK_FLAGS_IPO}")
  endif()
endif()

set(CMAKE_THREAD_PREFER_PTHREAD ON)
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

if (THREADS_HAVE_PTHREAD_ARG)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -pthread")
endif()

include(TdSetUpCompiler)
td_set_up_compiler()

if (CLANG OR GCC)
  if (MEMPROF)
    include(CheckCXXCompilerFlag)
    check_cxx_compiler_flag(-no-pie CXX_NO_PIE_FLAG)
    if (CXX_NO_PIE_FLAG)
      set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -no-pie")
    elseif (APPLE)
      set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -Wl,-no_pie")
    endif()
    include(AddCXXCompilerFlag)
    add_cxx_compiler_flag("-static-libstdc++")
    add_cxx_compiler_flag("-static-libgcc")
  endif()
endif()

set(BEHAPPY_BOT_API_SOURCE
  behappy-bot-api/telegram-bot-api.cpp

  behappy-bot-api/Client.cpp
  behappy-bot-api/ClientManager.cpp
  behappy-bot-api/HttpConnection.cpp
  behappy-bot-api/HttpStatConnection.cpp
  behappy-bot-api/Query.cpp
  behappy-bot-api/Stats.cpp
  behappy-bot-api/Watchdog.cpp
  behappy-bot-api/WebhookActor.cpp

  behappy-bot-api/Client.h
  behappy-bot-api/ClientManager.h
  behappy-bot-api/ClientParameters.h
  behappy-bot-api/HttpConnection.h
  behappy-bot-api/HttpServer.h
  behappy-bot-api/HttpStatConnection.h
  behappy-bot-api/Query.h
  behappy-bot-api/Stats.h
  behappy-bot-api/Watchdog.h
  behappy-bot-api/WebhookActor.h
)

add_executable(behappy-bot-api ${BEHAPPY_BOT_API_SOURCE})
target_include_directories(behappy-bot-api PRIVATE $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>)
target_link_libraries(behappy-bot-api PRIVATE memprof tdactor tdcore tddb tdnet tdutils)

install(TARGETS behappy-bot-api RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}")
if (MSVC AND VCPKG_TOOLCHAIN)
  install(DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/$<CONFIG>/" DESTINATION "${CMAKE_INSTALL_BINDIR}" FILES_MATCHING PATTERN "*.dll" PATTERN "*.pdb")
endif()
