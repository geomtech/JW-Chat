function bible_book_id(book) {

    const books = {
        "gen": 1,
        "exod": 2,
        "levi": 3,
        "nombr": 4,
        "deut": 5,
        "jos": 6,
        "juge": 7,
        "ruth": 8,
        "1sam": 9,
        "2sam": 10,
        "1rois": 11,
        "2rois": 12,
        "1chro": 13,
        "2chro": 14,
        "esd": 15,
        "neh": 16,
        "est": 17,
        "job": 18,
        "ps": 19,
        "pr": 20,
        "ecc": 21,
        "chant": 22,
        "isa": 23,
        "jér": 24,
        "lam": 25,
        "ez": 26,
        "da": 27,
        "os": 28,
        "joel": 29,
        "am": 30,
        "ab": 31,
        "jon": 32,
        "mi": 33,
        "na": 34,
        "haba": 35,
        "so": 36,
        "agg": 37,
        "zac": 38,
        "mal": 39,
        "mat": 40,
        "marc": 41,
        "luc": 42,
        "jean": 43,
        "acte": 44,
        "ro": 45,
        "1co": 46,
        "2co": 47,
        "ga": 48,
        "eph": 49,
        "philippien": 50,
        "col": 51,
        "1th": 52,
        "2th": 53,
        "1ti": 54,
        "2ti": 55,
        "1tm": 54,
        "2tm": 55,
        "tit": 56,
        "phi": 57,
        "héb": 58,
        "jac": 59, 
        "1pi": 60,
        "2pi": 61,
        "1je": 62,
        "2je": 63,
        "3je": 64,
        "jud": 65,
        "rev": 66
    }

    for (const [key, value] of Object.entries(books)) {
        if (book.startsWith(key.toLowerCase())) {
            return value;
        }
    }

    return null;
}

function bible_handler(message) {
    // Regex pattern to match references like "Jean 1:1", "Jean 1:1-6", "Jean 1:1, 6", "Jean 1:1, 3-5" ou "Hébreux 1:1"
    const versePattern = /\b([1-3]?\s?[A-Za-zÀ-ÿ]+)\s+(\d{1,3}):(\d{1,3}(?:-\d{1,3})?(?:,\s?\d{1,3}(?:-\d{1,3})?)*)\b/g;
    const jwOrgBaseUrl = "https://www.jw.org/finder?srcid=jwlshare&wtlocale=F&prefer=lang&bible=";

    return message.replace(versePattern, (match, book, chapter, verses) => {
        const bookId = bible_book_id(book.replace(' ', '').toLowerCase());
        const chapterPadded = chapter.padStart(3, '0');
        const verseRanges = verses.split(',').map(verseRange => verseRange.trim());
        const verseLinks = [];

        verseRanges.forEach((verseRange, index) => {
            const [startVerse, endVerse] = verseRange.split('-').map(v => v.trim());
            const startVersePadded = startVerse.padStart(3, '0');
            const endVersePadded = endVerse ? endVerse.padStart(3, '0') : startVersePadded;

            if (!endVerse && index < verseRanges.length - 1) {
                const nextVerseRange = verseRanges[index + 1].trim();
                const [nextStartVerse, nextEndVerse] = nextVerseRange.split('-').map(v => v.trim());

                if (!nextEndVerse && parseInt(nextStartVerse) === parseInt(startVerse) + 1) {
                    const nextStartVersePadded = nextStartVerse.padStart(3, '0');
                    verseLinks.push(`<a target="_blank" href="${jwOrgBaseUrl}${bookId}${chapterPadded}${startVersePadded}-${bookId}${chapterPadded}${nextStartVersePadded}&pub=nwtsty">${book} ${chapter}:${startVerse}, ${nextStartVerse}</a>`);
                    verseRanges.splice(index + 1, 1); // Remove the next verse from the array as it's already processed
                } else {
                    verseLinks.push(`<a target="_blank" href="${jwOrgBaseUrl}${bookId}${chapterPadded}${startVersePadded}-${bookId}${chapterPadded}${startVersePadded}&pub=nwtsty">${book} ${chapter}:${startVerse}</a>`);
                }
            } else {
                verseLinks.push(`<a target="_blank" href="${jwOrgBaseUrl}${bookId}${chapterPadded}${startVersePadded}-${bookId}${chapterPadded}${endVersePadded}&pub=nwtsty">${book} ${chapter}:${verseRange}</a>`);
            }
        });

        return verseLinks.join(', ');
    });
}