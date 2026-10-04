"use client";

import { Phone } from "lucide-react";

import { Button } from "@/components/ui/button";

/** MOHRE's call centre as a tap-to-call button: referral page and the "not sure" notice (task 8.5). */
export function MohreCall() {
  return (
    <Button asChild size="lg">
      <a href="tel:80084" dir="ltr">
        <Phone aria-hidden className="size-4" />
        80084
      </a>
    </Button>
  );
}
