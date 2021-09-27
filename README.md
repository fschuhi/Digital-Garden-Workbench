# Digital Workbench for Rob Burbea's Digital Garden
This is a collection of Python scripts to help curating the [Digital Garden of Rob Burbea's Teachings](http://publish.obsidian.md/rob-burbea), called from here just the "Digital Garden".

The Digital Garden is authored using [Obsidian](https://obsidian.md/), a knowledge management system organized in "notes", written in [Markdown](https://en.wikipedia.org/wiki/Markdown). Notes can refer to other notes, or headers or paragraphs on notes. 

The Obsidian desktop application works on a local set of notes. With the appropriate settings, the application can publish existing notes to the internet where anyone can access the published collection of notes with a browser like Chrome (best choice) or Firefox.^[At this point in time (Sep21), our Digital Garden is not officially mobile-ready. The Obsidian dev team is working on providing this functionality in one of the next releases.]

Internally, Obsidian organized the notes in "vaults". Any subset of pages of a vault can be earmarked for Obsidian Publish. There is one vault behind each site which is run by Obsidian Publish. Our Digital Garden is backed by the vault. You'll find the notes and other files (like images, PDFs and css) in [here](https://github.com/fschuhi/rob-burbea-digital-garden-publish). In the following, the latter is called "publish vault", as opposed to the "work vault" which is the one where day-to-day work with Obsidian is happening, including but not limited to the authoring of notes relating to the Digital Garden.

The workbench scripts are used to do the following on the raw Obsidian note:
* copy notes from the work to the publish vault
* transform work notes before copying them to the publish vault
* handling of the main keyword index with its index entry files
* automated generation of link sections (for transcript pages, for paragraphs, for citations on index entry pages)
* support for pagination of talk transcripts
* automatic creation of summary pages
* diacritics management and other tools to make the markdown uniform across all talks

This script adapts [jgclark's BibleGateway-to-Markdown](https://github.com/jgclark/BibleGateway-to-Markdown) script to export for use in [Obsidian](https://obsidian.md/). It accompanies a [Bible Study in Obsidian Kit](https://forum.obsidian.md/t/bible-study-in-obsidian-kit-including-the-bible-in-markdown/12503?u=selfire) that gets you hands-on with using Scripture in your personal notes.

What the script does is fetch the text from [Bible Gateway](https://www.biblegateway.com/) and save it as formatted markdown file. Each chapter is saved as one file and navigation between files as well as a book-file is automatically created. All of the chapter files of a book are saved in its numbered folder.

This script is intended to be as simple as possible to use, even if you have no idea about Scripting. If you have any questions, please reach out to me either on github or Discord (`selfire#3095`).
***
> You can help me keep creating tools like this by [buying me a coffee](https://www.buymeacoffee.com/joschua) ☕️.

<a href="https://www.buymeacoffee.com/joschua" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height= "48" width="173"></a>


## Important Disclaimers
Certain workbench scripts refer to "HAF", the [_Hermes Amara Foundation_](mailto:hermes.amara@gmail.com). HAF is a sangha-led organisation that was established to preserve and develop Rob's vast Dharma teaching legacy. HAF holds the rights to all of Rob's talks. You are invited to use the workbench for your own purposes. Note, though, that the workbench is very much in flux and heavily geared to be used for just one task: managing the [Digital Garden](http://publish.obsidian.md/rob-burbea), which is one of HAF's projects.

## Installation
(to be added soon)

## Usage
(to be added soon)
