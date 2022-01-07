#!/bin/sh
exec gunicorn -b :8000 --access-logfile - --error-logfile - face_mask_srv:app &
exec gunicorn -b :8010 --access-logfile - --error-logfile - face_feature_srv:app &
