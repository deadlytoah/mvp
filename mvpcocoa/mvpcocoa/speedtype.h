//
//  speedtype.h
//  mvpcocoa
//
//  Created by Heesuk Shin on 15/09/2018.
//  Copyright © 2018 Hee Suk Shin. All rights reserved.
//

#ifndef speedtype_h
#define speedtype_h

#include <stdint.h>

typedef size_t CharId;
typedef size_t WordId;

typedef struct {
    CharId id;
    uint32_t character;
    uint32_t whitespace;    // boolean
    uint32_t newline;       // boolean
    uint32_t has_word;      // boolean
    WordId word;
    uint32_t visible;       // boolean
    uint32_t has_typed;     // boolean
    uint32_t typed;
    uint32_t correct;       // boolean
    uint32_t rendered;       // boolean
} SpeedtypeCharRaw;

typedef struct {
    WordId id;
    const char *word;
    uint32_t visible;
    uint32_t touched;
    uint32_t behind;
    size_t characters_len;
    CharId *characters_ptr;
} SpeedtypeWordRaw;

typedef struct {
    size_t words_len;
    WordId *words_ptr;
} SpeedtypeSentenceRaw;

typedef struct {
    size_t buffer_len;
    SpeedtypeCharRaw *buffer_ptr;
    size_t words_len;
    SpeedtypeWordRaw *words_ptr;
    size_t sentences_len;
    SpeedtypeSentenceRaw *sentences_ptr;
} SpeedtypeStateRaw;

extern SpeedtypeStateRaw *speedtype_new();
extern void speedtype_delete(SpeedtypeStateRaw*);
extern int speedtype_process_line(SpeedtypeStateRaw*, const char*);
extern void speedtype_apply_level(SpeedtypeStateRaw*, unsigned char);

#endif /* speedtype_h */
