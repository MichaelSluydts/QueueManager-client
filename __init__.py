import os
from sys import exit
if not os.path.isfile(os.path.join(os.getenv('HOME'),'.highthroughput')):
    exit('Please log in to http://physics.epotentia.com/queue/ (request an account from Michael if you don\'t have one) then paste the contents of http://physics.epotentia.com/queue/HT.php in ~/.highthroughput and try again.')

__all__ = ['communication', 'manage', 'io','modules','utils','errors']
#import communication,manage,io,modules,utils,errors

