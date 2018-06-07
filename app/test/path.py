"""
경로 테스트
"""
import os

print(os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), './common'))