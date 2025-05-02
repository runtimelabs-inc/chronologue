// src/context/CalendarEventContext.tsx
import { createContext, useState, ReactNode } from 'react';

export const CalendarEventContext = createContext({
  events: [] as any[],
  addEvent: (event: any) => {},
});

export function CalendarEventProvider({ children }: { children: ReactNode }) {
  const [events, setEvents] = useState<any[]>([]);

  const addEvent = (event: any) => setEvents((prev) => [...prev, event]);

  return (
    <CalendarEventContext.Provider value={{ events, addEvent }}>
      {children}
    </CalendarEventContext.Provider>
  );
}
