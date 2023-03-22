# Python image to use.
FROM nikolaik/python-nodejs:latest
ENV NODE_ENV=production

# Set the working directory to /app
WORKDIR /app

# copy the requirements file used for dependencies
COPY requirements.txt .
COPY package.json .
COPY tailwind.config.js .
# Copy the rest of the working directory contents into the container at /app
COPY . .

RUN npm install --production

RUN npx tailwindcss -i ./static/src/input.css -o ./static/dist/css/output.css --watch

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt


# Run app.py when the container launches
ENTRYPOINT ["python", "app.py"]
