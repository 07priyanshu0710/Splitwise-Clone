import { cn } from "@/lib/utils";

export function NeoInput({ className, label, error, ...props }) {
  return (
    <div className="w-full flex flex-col gap-2">
      {label && (
        <label className="font-bold text-sm uppercase tracking-widest text-black">
          {label}
        </label>
      )}
      <input
        className={cn(
          "h-14 w-full bg-white border-4 border-black px-4 font-bold text-lg text-black placeholder:text-black/40 outline-none transition-all duration-100 rounded-none",
          "focus-visible:bg-neo-secondary focus-visible:shadow-neo",
          error && "border-neo-accent focus-visible:bg-red-50",
          className
        )}
        {...props}
      />
      {error && (
        <p className="text-neo-accent font-bold text-sm mt-1">{error}</p>
      )}
    </div>
  );
}
