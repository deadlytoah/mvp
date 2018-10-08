//
//  session.h
//  mvpcocoa
//
//  Created by Chris Heesuk Shin on 07/08/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

#ifndef session_h
#define session_h

#include <unistd.h>

typedef struct {
    unsigned char translation[8];
    unsigned char book[8];
    unsigned short chapter;
    unsigned short sentence;
    unsigned short verse;
} LocationRaw;

typedef struct {
    unsigned char name[32];
    LocationRaw range[2];
    unsigned char level;
    unsigned char strategy;
} SessionRaw;

typedef struct {
    unsigned char key[16];
    unsigned char text[496];
} VerseRaw;

typedef struct {
    size_t count;
    VerseRaw verses[176];
} VerseView;

typedef struct {
    size_t index;
    size_t length;
} LayoutLine;

typedef enum {
    VerseSourceBlueLetterBible
} VerseSource;

typedef struct {
    unsigned char text[1024];
} SentenceRaw;

extern int session_create(SessionRaw *);
extern int session_list_sessions(SessionRaw *buf, size_t *len);
extern int session_delete(SessionRaw *);
extern char *const session_get_message(int error_code);

extern void sentences_from_verses(const char **verses_ptr,
                                  size_t verses_len,
                                  SentenceRaw *sentences_ptr,
                                  size_t *sentences_len);

extern int verse_find_all(const char *translation, VerseView *view);
extern int verse_find_by_book_and_chapter(const char *translation,
                                          VerseView *view,
                                          const char *book,
                                          unsigned short chapter);
extern int verse_fetch_by_book_and_chapter(const char *translation,
                                           VerseView *view,
                                           VerseSource source,
                                           const char *book,
                                           unsigned short chapter);
extern int verse_insert(const char *translation,
                        const VerseView *view,
                        const char *book,
                        unsigned short chapter);

extern int cache_create(const char *translation);

extern int graphlayout_layout(const char *text,
                              LayoutLine *indicies_ptr,
                              size_t *indicies_len);

#endif /* session_h */
