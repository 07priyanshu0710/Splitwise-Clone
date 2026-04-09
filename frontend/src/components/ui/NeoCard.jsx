import { cn } from "@/lib/utils";

export function NeoCard({ children, className, hover = true, ...props }) {
  return (
    <div
      className={cn(
        "bg-white border-4 border-black shadow-neo transition-all duration-200 rounded-none",
        hover && "hover:-translate-y-2 hover:shadow-neo-xl",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
