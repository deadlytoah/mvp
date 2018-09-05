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
} Location;

typedef struct {
    unsigned char name[64];
    Location range[2];
    unsigned char level;
    unsigned char strategy;
} Session;

extern int session_create(Session *);
extern int session_list_sessions(Session *buf, size_t *len);
extern int session_delete(Session *);
extern char *const session_get_message(int error_code);

#endif /* session_h */
