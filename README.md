# Digital Workbench for Rob Burbea's Digital Garden
This is a collection of Python scripts for the [Digital Garden of Rob Burbea's Teachings](http://publish.obsidian.md/rob-burbea] (from here on call just "Digital Garden".)

Certain workbench scripts refer to "HAF", the [_Hermes Amara Foundation_](mailto:hermes.amara@gmail.com). HAF is a sangha-led organisation that was established to preserve and develop [Rob](https://publish.obsidian.md/rob-burbea/Rob+Burbea)'s vast Dharma teaching legacy. HAF holds the rights to all of Rob's talks. You are invited to use the workbench for your own purposes. Note, though, that the workbench is very much in flux and heavily geared to be used for just one task: managing the Digital Garden.

The Digital Garden is authored using [Obsidian](https://obsidian.md/), a knowledge management system organized in "notes", written in [Markdown](https://en.wikipedia.org/wiki/Markdown). Notes can refer to other notes, or headers or paragraphs on notes. The notes and the links and backlinks between them form a semantic network. 

The Obsidian desktop application works on a local set of notes. With the appropriate settings, the application can publish existing notes to the internet where anyone can access the published collection of notes with a browser like Chrome (best choice) or Firefox.^[At this point in time (Sep21), our Digital Garden is not officially mobile-ready. The Obsidian dev team is working on providing this functionality in one of the next releases.]

Obsidian Publish is a cloud service operated by Obsidian, the team behind [Obsidian](https://obsidian.md). Obsidian Publish takes the files from the publish vault and displays them as pages in the [Digital Garden]http://publish.obsidian.md/rob-burbea).

Internally, the Obsidian desktop application organizes the notes in "vaults". In the context of the Digital Garden, there are two vaults:
* the _work vault_, which is the one where day-to-day work with Obsidian is happening, including but not limited to the authoring of notes relating to the Digital Garden, and
* the _publish vault_, which contains a subset of (possibly transformed) notes from the work vault.

The contents of the publish vault can be found [here](https://github.com/fschuhi/rob-burbea-digital-garden-publish).

The workbench is a command line tool to help the ["gardening"](https://publish.obsidian.md/rob-burbea/Gardening):

```console
S:\python HAFScripts.py
```

For the possible switches see the *.py

Among others, the workbench is used for the following tasks:
* copy notes from the work to the publish vault
* transcribe certain parts of notes to manage the UX of the Digital Garden
* manage the main keyword index with its index entry files
* generate link sections (for transcript pages, for paragraphs, for citations on index entry pages)
* manage breadcrumbs in summaries
* paginate new talk transcripts
* initialize new talk series
* create skeleton notes for talk summaries
* handle diacritics
* transform tools to transformation tools to make the markdown uniform across all talks

