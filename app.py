from flask import Flask, render_template
import os
import docx

app = Flask(__name__)

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
    if not os.path.exists(BLOGS_FOLDER):
        print(f"Error: The folder {BLOGS_FOLDER} does not exist.")
        return blogs

    for filename in os.listdir(BLOGS_FOLDER):
        if filename.endswith('.docx'):
            file_path = os.path.join(BLOGS_FOLDER, filename)
            try:
                blog_data = read_docx(file_path)
                blogs.append(blog_data)
            except ValueError as e:
                print(f"Error reading {filename}: {e}")
    return blogs


# Home route
@app.route('/')
def home():
    blogs = get_blogs()
    return render_template('home.html', blogs=blogs)

# Blog post route
@app.route('/blog/<int:blog_id>')
def blog(blog_id):
    blogs = get_blogs()
    post = blogs[blog_id]
    return render_template('blog.html', post=post)

if __name__ == "__main__":
    app.run(debug=True)
