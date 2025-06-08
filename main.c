#include "opencplc.h" // Import funkcji sterownika
#include "exmath.h"

struct {
  float start;
  float min;
  float end;
  float max;
  float ramp;
  float rest;
  float step_delta;
  float ema_alpha;
  float dither;
  float idle_time;
  struct {
    float value;
    float during;
    float interval;
  } preserv;
} cfg;

typedef enum {
  CHAN_None = 0,
  CHAN_1 = 1,
  CHAN_2 = 2
} CHAN_t;

void disable_valves(void)
{
  DOUT_Duty(&TO1, cfg.min * cfg.rest);
  DOUT_Duty(&TO2, cfg.min * cfg.rest);
  DOUT_Rst(&RO1);
}

void loop(void)
{

  cfg.step_delta = 0.1;
  cfg.ema_alpha = 0.1;


  float prev_step = 0;
  float prev_ema = 0;

  while(1) {
    // uint64_t tick = tick_keep(5);

    cfg.start = POT_Normalized(&POT1) / 2;
    cfg.min = POT_Percent(&POT2) / 2;
    cfg.end = (POT_Normalized(&POT3) / 2) + 0.5;
    cfg.max = (POT_Percent(&POT4) / 2) + 50.0;
    cfg.ramp = (pow(POT_Normalized(&POT5), 4.0) * 4.8) + 0.2;
    cfg.rest = POT_Normalized(&POT6) / 2;

    float in = AIN_Normalized(&DI1);
    if(AIN_Value_Error(in)) {
      // potencjometr odpięty
      LOG_Error("Potentiometer is disconnected");
      continue;
    }
    prev_step = step_limiter_float(in, prev_step, cfg.step_delta);
    prev_ema = ema_filter_float(prev_step, prev_ema, cfg.ema_alpha);
    in = prev_ema;
    in = (in * 2) - 1.0; // Przeskalowanie sygnału wejściowego do zakresu -1..1
    CHAN_t chan = CHAN_None;
    if(in >= cfg.start) { chan = CHAN_1; } // Obsługa zaworu 1
    else if(in <= -cfg.start) { chan = CHAN_2; in *= -1; } // Obsługa zaworu 2
    else { disable_valves(); continue; } // Martwa strefa – zawory pozostają wyłączone
    if(!DIN_State(&DI1)) {
      // Brak sygnału zezwolenia na aktywację
      LOG_Warning("Missing enable signal, but the potentiometer indicates activation");
      disable_valves();
      continue;
    }
    float a = (cfg.max - cfg.min) / (cfg.end - cfg.start);
    float b = cfg.min - (a * cfg.start);
    float out = pow(in, cfg.ramp) * a + b; // Przeliczenie wartości `in` (x) na `out` (y)
    if(out > cfg.max) out = cfg.max; // Ograniczenie wartości do `cfg.max`
    if(chan == CHAN_1) { // Aktywacja zaworu 1, wyłączenie zaworu 2
      DOUT_Duty(&TO1, out);
      DOUT_Duty(&TO2, cfg.min * cfg.rest);
    }
    else if(chan == CHAN_2) { // Aktywacja zaworu 2, wyłączenie zaworu 1
      DOUT_Duty(&TO1, cfg.min * cfg.rest);
      DOUT_Duty(&TO2, out);
    }
    DOUT_Set(&RO1);
  }
}




stack(stack_plc, 256); // Stos pamięci dla wątku PLC
stack(stack_dbg, 256); // Stos pamięci dla wątku debug'era (logs + bash)
stack(stack_loop, 1024); // Stos pamięci dla funkcji loop

int main(void)
{
  thread(PLC_Thread, stack_plc); // Dodanie wątku sterownika
  thread(DBG_Loop, stack_dbg); // Dodanie wątku debug'era (logs + bash)
  thread(loop, stack_loop); // Dodanie funkcji loop jako wątek
  vrts_init(); // Włączenie systemy przełączania wątków VRTS
  while(1); // W to miejsce program nigdy nie powinien dojść
}