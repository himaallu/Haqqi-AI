import * as React from "react";

import { cn } from "@/lib/utils";

const control =
  "w-full min-h-11 rounded-md border border-input bg-background px-3 py-2 text-base shadow-xs outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-destructive/20";

function Input({ className, ...props }: React.ComponentProps<"input">) {
  return <input data-slot="input" className={cn(control, className)} {...props} />;
}

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return <textarea data-slot="textarea" className={cn(control, "min-h-40 leading-relaxed", className)} {...props} />;
}

/** A native select: phones show their own large, accessible picker. */
function Select({ className, ...props }: React.ComponentProps<"select">) {
  return <select data-slot="select" className={cn(control, "appearance-auto", className)} {...props} />;
}

function Label({ className, ...props }: React.ComponentProps<"label">) {
  return <label data-slot="label" className={cn("text-sm font-medium leading-snug", className)} {...props} />;
}

export { Input, Label, Select, Textarea };
