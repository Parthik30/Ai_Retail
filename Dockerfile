# Use the official Python 3.11 slim image
FROM python:3.11-slim

# Set up the working directory and user for Hugging Face Spaces
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Install dependencies (do this first to leverage Docker cache)
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create the Streamlit configuration for Hugging Face integration
RUN mkdir -p $HOME/.streamlit && \
    echo "[server]\nheadless = true\nport = 7860\nenableCORS = false\naddress = \"0.0.0.0\"\n" > $HOME/.streamlit/config.toml

# Copy project files
COPY --chown=user . $HOME/app

# Expose port and start Streamlit
EXPOSE 7860
CMD ["streamlit", "run", "backend/streamlit_app/app.py"]
