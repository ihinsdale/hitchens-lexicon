natural language processing of the writings of Christopher Hitchens
=================================================================================

![Hitchens at Victoria Falls](https://raw.github.com/ihinsdale/hitchens-lexicon/master/images/hitchens_at_falls.jpg)

## Table of Contents

* [Description](#description)
* [Documentation](#documentation)
* [Stack](#stack)
* [License](#license)

##<a name="description"></a>Description

This project collects the writings of Christopher Hitchens for natural language processing. The goal is to enable fans of Hitchens to analyze the corpus of his writing and discover things like:

- trends in the topics he wrote about
- favored words and phrases
- the size of his vocabulary

Currently, the collection only contains Hitchens' writings from 2002 - 2011 in Slate (his [Fighting Words](http://www.slate.com/authors.christopher_hitchens.html) column). Words from this corpus which Hitchens only ever used once -- [hapax legomena](http://en.wikipedia.org/wiki/Hapax_legomenon) -- are being tweeted by [@HitchensHapaxes](https://twitter.com/hitchenshapaxes).

Contributions are welcome! Hitchens' writings from a number of places remain to be scraped and added to the database:

- Vanity Fair
- The Atlantic
- London Review of Books
- The Nation
- New Statesman
- misc.

To complete the collection, his books should also be added. An interesting extension of the project would be to add the text of his speeches.

##<a name="documentation"></a>Documentation

`slate_scraper.py` scrapes the Slate archive of Hitchens' columns and stores their text in string and tokenized form in the database.

`bot.py` powers the @HitchensHapaxes Twitter bot. It extracts all of Hitchens' columns from the database, identifies all of the hapaxes, picks a random one, fetches its definition from Google and the context in which Hitchens used it, and tweets.

`tweet.sh` is the shell script for the executing `bot.py` as a cron job.

`setup.sh` is the shell script for configuring the Ubuntu 12.04 LTS cloud server on which the bot runs.

The database table in which writings are stored is created with the following command in the `psql` client:

    CREATE TABLE documents (id serial primary key, url text, title text, subtitle text, publication_date date, content text, content_tokenized text[]);

##<a name="stack"></a>Stack

Hitchens' writings are stored in a PostgreSQL database and analyzed using the Python library [nltk](http://nltk.org).

![Python](https://raw.github.com/ihinsdale/hitchens-lexicon/master/images/python-logo.jpg)

![PostgreSQL](https://raw.github.com/ihinsdale/hitchens-lexicon/master/images/postgresql_logo-100px.png)

##<a name="license"></a>License

See LICENSE.md.

