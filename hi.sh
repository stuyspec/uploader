#!/bin/bash
for i in {1..14}
do
    http PUT :3000/media/$i url='https://avatars1.githubusercontent.com/u/15334952?s=400&u=01656ec69d454e9792ce69c88a1563fd58bca750&v=4'
done
