/**
 * Calendário semanal – Alpine.js component.
 * Grade Seg–Dom, 08:00–17:30 (slots de 30 min).
 * Eventos carregados via /agenda/api/week/?week_start=YYYY-MM-DD
 */
function weeklyCalendar() {
  var DAY_LABELS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];
  var HOUR_START = 7;
  var HOUR_END = 22;  // último slot: 22:30
  var SLOT_HEIGHT = 32; // px

  var COLORS = [
    'bg-blue-100 border-blue-500 text-blue-900',
    'bg-green-100 border-green-500 text-green-900',
    'bg-yellow-100 border-yellow-500 text-yellow-900',
    'bg-purple-100 border-purple-500 text-purple-900',
    'bg-pink-100 border-pink-500 text-pink-900',
    'bg-teal-100 border-teal-500 text-teal-900',
    'bg-orange-100 border-orange-500 text-orange-900',
    'bg-indigo-100 border-indigo-500 text-indigo-900'
  ];

  return {
    loading: false,
    weekStart: null,
    rawEvents: [],
    processedEvents: [],
    days: [],
    timeSlots: [],
    weekLabel: '',
    _timer: null,

    init: function() {
      // Gerar time slots (08:00, 08:30, 09:00, ... 17:30)
      this.timeSlots = [];
      for (var h = HOUR_START; h <= HOUR_END; h++) {
        this.timeSlots.push({ hour: h, half: 0, label: String(h).padStart(2, '0') + ':00' });
        this.timeSlots.push({ hour: h, half: 30, label: String(h).padStart(2, '0') + ':30' });
      }
      this.goToday();
    },

    goToday: function() {
      var today = new Date();
      var dow = today.getDay();
      var diff = dow === 0 ? -6 : 1 - dow;
      var mon = new Date(today);
      mon.setDate(today.getDate() + diff);
      mon.setHours(0, 0, 0, 0);
      this.weekStart = mon;
      this._loadWeek();
    },

    prevWeek: function() {
      var d = new Date(this.weekStart);
      d.setDate(d.getDate() - 7);
      this.weekStart = d;
      this._loadWeek();
    },

    nextWeek: function() {
      var d = new Date(this.weekStart);
      d.setDate(d.getDate() + 7);
      this.weekStart = d;
      this._loadWeek();
    },

    isToday: function(dayIdx) {
      if (!this.days[dayIdx]) return false;
      var today = new Date();
      var d = this.days[dayIdx].date;
      return d.getFullYear() === today.getFullYear() &&
             d.getMonth() === today.getMonth() &&
             d.getDate() === today.getDate();
    },

    _loadWeek: function() {
      var self = this;
      self.loading = true;

      // Build days array
      self.days = [];
      for (var i = 0; i < 7; i++) {
        var d = new Date(self.weekStart);
        d.setDate(d.getDate() + i);
        self.days.push({
          label: DAY_LABELS[i],
          number: d.getDate(),
          date: d
        });
      }

      // Week label
      var fmt = function(dt) {
        return dt.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
      };
      self.weekLabel = fmt(self.weekStart) + ' — ' + fmt(self.days[6].date);

      // Fetch events
      var y = self.weekStart.getFullYear();
      var m = String(self.weekStart.getMonth() + 1).padStart(2, '0');
      var dd = String(self.weekStart.getDate()).padStart(2, '0');
      var wsISO = y + '-' + m + '-' + dd;

      fetch('/agenda/api/week/?week_start=' + wsISO, {
        credentials: 'same-origin'
      })
      .then(function(resp) {
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        return resp.json();
      })
      .then(function(data) {
        self.rawEvents = data.events || [];
        console.log('[Calendário] Semana:', wsISO, '| Eventos recebidos:', self.rawEvents.length, self.rawEvents);
        self._processEvents();
        console.log('[Calendário] Eventos processados:', self.processedEvents.length, self.processedEvents);
        self.loading = false;
      })
      .catch(function(err) {
        console.error('[Calendário] Erro ao carregar:', err);
        self.rawEvents = [];
        self.processedEvents = [];
        self.loading = false;
      });
    },

    _processEvents: function() {
      var self = this;
      self.processedEvents = [];

      self.rawEvents.forEach(function(ev, idx) {
        var start = new Date(ev.start);
        var end = new Date(ev.end);

        // Calcular dia da semana a partir do JS (timezone local do browser)
        // JS: getDay() → 0=Dom, 1=Seg, ..., 6=Sáb
        // Converter para 0=Seg, 6=Dom
        var jsDay = start.getDay();
        var dayIdx = jsDay === 0 ? 6 : jsDay - 1;

        // Slot do início: hora e meia-hora
        var startHour = start.getHours();
        var startHalf = start.getMinutes() >= 30 ? 30 : 0;

        // Calcular duração em slots de 30min
        var durationMs = end.getTime() - start.getTime();
        var durationSlots = Math.max(1, Math.round(durationMs / (30 * 60 * 1000)));

        var startH = String(start.getHours()).padStart(2, '0');
        var startM = String(start.getMinutes()).padStart(2, '0');
        var endH = String(end.getHours()).padStart(2, '0');
        var endM = String(end.getMinutes()).padStart(2, '0');
        var timeLabel = startH + ':' + startM + ' – ' + endH + ':' + endM;

        var colorClass = ev.confirmed
          ? COLORS[idx % COLORS.length]
          : 'bg-gray-100 border-gray-400 text-gray-600';

        self.processedEvents.push({
          id: ev.id,
          title: ev.title,
          client: ev.client || '',
          day: dayIdx,
          startHour: startHour,
          startHalf: startHalf,
          cellSpan: durationSlots,
          timeLabel: timeLabel,
          tooltip: ev.title + (ev.client ? ' — ' + ev.client : '') + ' (' + timeLabel + ')',
          colorClass: colorClass
        });
      });
    },

    getEventsForCell: function(dayIdx, hour, half) {
      return this.processedEvents.filter(function(ev) {
        return ev.day === dayIdx && ev.startHour === hour && ev.startHalf === half;
      });
    }
  };
}
