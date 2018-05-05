# Uploading

### Table of Contents
Topic | Description
:---:| ---
[Issue Folder Prep](#issue-folder-prep) | How to prep and clean an issue folder to minimize uploading errors and mistakes
[Manual Upload](#manual-upload) | Uploader failed? How to create an article with Rails console

------

## Issue Folder Prep

_Note: You need to know regex to understand these instructions. Any developer should know/learn regex._

1. Make sure the following files are direct children of the issue folder and have names that match these patterns:
- Newspaper PDF: `(?i)Issue\s?\d{1,2}(\.pdf)$`
- SBC ("seen by copy"/final drafts) folder: `SBC`
- Photo Color folder: `(?i)photo\s?color`
- Art folder: `(?i)art`

2. Make sure all photos you intend to use are the **direct children** of the Photo Color folder. For instance, SING! photos may be grouped in a folder inside Photo Color—move them outside.

3. Ensure that all department folders in SBC are spelled correctly. (The editors like to meme sometimes.)

4. For EVERY non-ignored Google Doc article (ignored Docs have filenames that match this pattern: `(?i)worldbeat|survey|newsbeat|spookbeat|playlist|calendar|\[IGNORE\]`):
- Below the title must be the article label. Those look something like: `The Spectator/Humor/Issue 14`.
- Make sure the end of the slug (a.k.a. article header) looks like it's part of the header (e.g. the line is a focus sentence, word count, byline, etc.) This is the exact pattern for an element of a slug:
```
(?i)(outquote(\(s\))?s?:)|(focus\s+sentence:)|(word(s)?:?\s\d{2,4})|(\d{2,4}\swords[^\.])|(word count:?\s?\d{2,4})|focus:|article:|(Art|Photo)(\/Art|\/Photo)? Request:?
```
In the below example, the focus sentence needs to be moved below the outquotes because the second outquote could actually be part of the article. If there were no focus sentence, "1111 words" could also be moved below the outquote.
```
Art’s Accessibility is Technically Amazing
The Spectator / A&E / Issue 12
By Jacqueline Thom and Andrew Ng
jthom00@stuy.edu, ang00@stuy.edu
1111 words
Focus Sentence: Art is an enriching experience.
Outquotes: Creating art is no longer being limited.
There are numerous artists who embrace non-traditional mediums.
```
-  Any emphasized text needs to be wrapped in hypertext markup.
  * `<t></t>`: indent, useful for faking a `<ul>` (hopefully we'll add `<ul>` into this list at a later point)
  * `<hr/>`: horizontal rule/line, often used to separate footer notes from content
  * `<h5> ... </h5>`: bold and uppercase
  * `<h4> ... </h4>`: bold, uppercase, and centered
 
5. Resolve all comments and suggestions.

6. There MUST be a byline, and it MUST start with the word "By". If no byline exists, add "By The XXX Department" to the slug. (Spell A&E by its full name, Arts & Entertainment.)

7. To ignore an article, put [IGNORE] in the filename ([example](https://docs.google.com/document/d/1Mxiiiq6KShSGRP446Hnvhh6U1Q0Rkz9CMnUVEXLoeO8/edit?usp=sharing)).

### Special Cases

#### Disrespectator

Move all Disrespectator articles into the Humor folder of SBC.

_Note: After changing any file structure (NOT FILE CONTENT), the changes will not appear in the uploader until you use the `--reload, -r` flag to reload them. This will take a while (almost 30 seconds) so reload minimally._

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
