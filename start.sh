#!/bin/bash
# Serve the document visualizer

gunicorn visualizer.app:__hug_wsgi__
