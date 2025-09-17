FROM gcr.io/oss-fuzz-base/base-builder-jvm

RUN apt-get update && apt-get install -y maven

# Copy all content of the project
COPY . /src/

# Set the working directory
WORKDIR /src