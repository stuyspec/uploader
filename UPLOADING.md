# Uploading

### Table of Contents
Topic | Description
:---:| ---
[Issue Folder Prep](#issue-folder-prep) | How to prep and clean an issue folder to minimize uploading errors and mistakes
[Manual Upload](#manual-upload) | Uploader failed? How to create an article with Rails console

------

## Issue Folder Prep

_Note: You need to know regex to understand these instructions. Any developer should know/learn regex._

1. Make sure the following files will match these patterns in the issue folder:
- Newspaper PDF: `(?i)Issue\s?\d{1,2}(\.pdf)$`
- SBC ("seen by copy"/final drafts) folder: `SBC`
- Photo Color folder: `(?i)photo\s?color`
- Art folder: `(?i)art`

2. Also make sure all photos you intend to use are the **direct children** of the Photo Color folder. For instance, SING! photos may be grouped in a folder inside Photo Color—move them outside.

_Note: After changing any file structure (NOT FILE CONTENT), the changes will not appear in the uploader until you use the `--reload, -r` flag to reload them. This will take a while (almost 40 seconds) so reload minimally._

------

## Manual Upload

1. In the Rails console (setup instructions on the [API's README](https://github.com/stuyspec/stuy-spec-api)) create an article:
```rb
> a = Article.new
```

2. Set the title of the article. Write a slug (yourself) as well.
```rb
> a.title = "National Walkout: An Act of Disobedience"
> a.slug = "national-walkout-an-act-of-disobedience"
```

3. Set the volume and issue of the article.
```rb
> a.volume = 108
> a.issue = 11 # Replace with current issue
```

4. Open a separate terminal instance. Open a Python shell to convert all content into paragraph form. The function below should take as its argument the content of the article (does not include any headers like "Focus sentence..." or "Outquotes...")
```py
def textToP(content):  
  content = filter(None, content.split('\n')) # Separates paragraphs and removes all empty lines  
  content = [x.strip() for x in content] # Removes any unnecessary spaces in paragraphs
 
  # We use print in lieu of return because return will give us the raw string 
  # (with non-ASCII characters in bit format) whereas print will print unicode.
  print '<p>' + '</p><p>'.join(content) + '</p>'
```

5. Copy what the function provides. Go back to the Rails console and add the paragraph'd content to the article.
```
> a.content = "[PASTE]"
```

6. Set the `section_id` of the article.
```rb
# Find the section you want
> Section.find_by(name: "Arts & Entertainment")
# Returns <Section id: 4...

# Here is a quick cheat sheet for section ID's:
# News: 1
# Opinions: 2
# Features: 3
# Arts & Entertainment: 4
# Humor: 5
# Sports: 6

> a.section_id = 4
```

7. For each contributor, find his or her `User` record (`User.find_by(last_name: "...")`) and use that ID to create an authorship.
```rb
> a.authorships.build(user_id: NN)
```

If the user does not exist, create one, then use the resulting ID for the Authorship.
```rb
> pword = (0...8).map { (65 + rand(26)).chr }.join
> u = User.create(first_name: "Jason", last_name: "Kao", email: "jkao1@stuy.edu", password: "pword", password_confirmation: "pword")
```

8. Save the article.
```rb
> a.save!
```

9. Visit the website to make sure everything uploaded correctly. If you made a small mistake in, for instance, the title, fix it by using the `update` method (it also automatically saves):
```rb
> a.update(title: "Fixed Title")
```

If your upload colosally failed, destroy the article (`destroy` deletes all associated records of the article (e.g. authorships, media) whereas `delete` only deletes the article).
```rb
> a.destroy
```
