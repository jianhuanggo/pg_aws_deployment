#yum install vi tar xz wget -y
#docker pull linuxserver/ffmpeg
#goto https://johnvansickle.com/ffmpeg/
#wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz

#tar xf ffmpeg-release-amd64-static.tar.xz

FROM public.ecr.aws/lambda/python:3.11
RUN yum update -y
RUN yum install vi tar xz wget -y
COPY . .
#RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
#RUN tar xf ffmpeg-release-amd64-static.tar.xz
#RUN cp ffmpeg-6.1-amd64-static/ffmpeg /usr/local/bin/

#RUN yum update -y && yum install ffmpeg -y
RUN pip install -r requirements.txt
CMD ["lambda_function.lambda_handler"]