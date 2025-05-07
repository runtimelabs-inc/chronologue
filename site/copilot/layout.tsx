import { CalendarEventProvider } from '@/context/CalendarEventContext';

export default function App({ Component, pageProps }) {
  return (
    <CalendarEventProvider>
      <Component {...pageProps} />
    </CalendarEventProvider>
  );
}
