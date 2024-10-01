from flask import Flask, render_template, request, jsonify
import os
import docx
from transformers import BartForConditionalGeneration, BartTokenizer
import torch

app = Flask(__name__)

# Load pre-trained BART model and tokenizer from Hugging Face
model = BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn')
tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')

# Path to the folder containing Word (.docx) files
BLOGS_FOLDER = 'blogs'

# Function to read .docx file content and extract metadata
def read_docx(file_path):
    doc = docx.Document(file_path)
    paragraphs = doc.paragraphs

    if len(paragraphs) < 4:
        raise ValueError("Document format is incorrect. Please include Title, Author, Date, and Content.")

    # Extract metadata from the first few lines
    title = paragraphs[0].text.replace("Title: ", "").strip()
    author = paragraphs[1].text.replace("Author: ", "").strip()
    date = paragraphs[2].text.replace("Date: ", "").strip()

    # Extract the content of the blog (remaining paragraphs)
    content = '\n'.join([p.text for p in paragraphs[3:]])

    return {
        "title": title,
        "author": author,
        "date": date,
        "content": content
    }

def get_blogs():
    blogs = []
    for filename in os.listdir(BLOGS_FOLDER):
        if filename.endswith('.docx'):
            file_path = os.path.join(BLOGS_FOLDER, filename)
            try:
                blog_data = read_docx(file_path)
                blogs.append(blog_data)
            except ValueError as e:
                print(f"Error reading {filename}: {e}")
    return blogs

def summarize_blog_post_bart(blog_content):
    """
    Summarize the input blog content using the BART model from Hugging Face.
    """
    # Tokenize the blog content
    inputs = tokenizer([blog_content], max_length=1024, return_tensors='pt', truncation=True)

    # Generate the summary with constraints for minimum and maximum length
    summary_ids = model.generate(
        inputs['input_ids'],
        num_beams=4,
        max_length=150,
        min_length=40,
        length_penalty=2.0,
        early_stopping=True
    )

    # Decode the summary
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    return summary

@app.route('/')
def home():
    blogs = get_blogs()
    return render_template('home.html', blogs=blogs)

@app.route('/blog/<int:blog_id>')
def blog(blog_id):
    blogs = get_blogs()
    post = blogs[blog_id]
    return render_template('blog.html', post=post)

@app.route('/summarize', methods=['POST'])
def summarize():
    """
    Summarize the blog content based on the blog ID provided.
    """
    try:
        # Get the blog ID from the POST request
        blog_id = int(request.form.get('blog_id'))

        # Retrieve the blog post using the ID
        blogs = get_blogs()
        if blog_id < 0 or blog_id >= len(blogs):
            return jsonify({'error': 'Invalid blog ID'}), 400

        blog_content = blogs[blog_id]['content']

        # Generate the summary
        summary = summarize_blog_post_bart(blog_content)

        # Return the summary as JSON
        return jsonify({'summary': summary}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)