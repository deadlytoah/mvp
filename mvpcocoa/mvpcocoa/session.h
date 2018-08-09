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

typedef struct Session Session;

extern Session *session_new(const char *name);
extern void session_delete(Session *);
extern int session_write(Session *);
extern int session_set_range(Session *, Location *start, Location *end);
extern int session_set_level(Session *, int level);
extern int session_set_strategy(Session *, int strategy);
extern int session_list_sessions(char *buf, size_t *len);
extern char *const session_get_message(int error_code);

#endif /* session_h */
