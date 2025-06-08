/**
 * @name  Projekt: demo/valves
 * @brief Podstawowe informacje projektowe '#define PRO_x'.
 *        Informacje te są wykorzystywane przez program wizard podczas ładowania projektu.
 *        Nie należy ich usuwać, jednak można je edytować.
 *        Zmiana tych parametrów wymaga ponownego wywołania programu Wizard.
 * @date  2025-05-20
 */

#ifndef PRO_x
#define PRO_x

#define PRO_BOARD_ECO
#define PRO_CHIP_STM32G0C1
#define PRO_VERSION         "develop"
#define PRO_USER_MEMORY_KB  20
#define PRO_OPT_LEVEL       "Og"

#endif

/**
 * @brief W tym pliku należy umieścić parametry konfiguracyjne '#define', które chce się nadpisać.
 * @note  Wiele z bibliotek załącza ten plik '#include', zatem musi on istnieć, nawet jeśli będzie pusty.
 *        Dzięki takiemu rozwiązaniu można nadpisać różnego rodzaju definicje (zmienne) konfiguracyjne.
 *        Biblioteki w pierwszej kolejności będą pobierały definicje zawarte tutaj,
 *        zamiast korzystać z domyślnych wartości zawartych we własnych plikach nagłówkowych '.h'.
 *        Ten mechanizm można również zastosować w swoich projektach, używając dyrektyw warunkowych #ifndef
 *        i dołączając plik main.h w celu nadpisania domyślnych definicji.​
 */

#define LOG_LEVEL       LOG_LEVEL_INF
#define SYS_CLOCK_FREQ  59904000