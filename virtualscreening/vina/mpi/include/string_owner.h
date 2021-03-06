#ifndef OLD_STRING_OWNER_H
#define OLD_STRING_OWNER_H


void int2str(char *str, const int *number);
int str2int(__const char *str);
float str2float(__const char *__str);
double str2double(__const char *str);
int length_char(const char *__str);
void append_char(char *dest, __const char *source, int max_num);
void substring(char *dest, const char __source[], int begin, int end);
void trim (char *str);
void rtrim (char *str);
void ltrim (char *str);
void remove_character(char *str, const char ch);
void remove_character_enter(char *str);
boolean_t is_equal(const char *c1, const char *c2);
boolean_t is_letter(const char letter);

#endif