import { useEffect, useState } from "react";
import { formatRelativeTime } from "@/utils/format";

interface RelativeTimeProps {
  date: string;
  className?: string;
}

export function RelativeTime({ date, className }: RelativeTimeProps) {
  const [display, setDisplay] = useState(() => formatRelativeTime(date));

  useEffect(() => {
    setDisplay(formatRelativeTime(date));
    const interval = setInterval(() => {
      setDisplay(formatRelativeTime(date));
    }, 1000);
    return () => clearInterval(interval);
  }, [date]);

  return (
    <time
      dateTime={date}
      title={new Date(date.endsWith("Z") || date.includes("+") ? date : date + "Z").toLocaleString()}
      className={className}
    >
      {display}
    </time>
  );
}
