"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label, Select } from "@/components/ui/field";
import { ApiError, confirmCase } from "@/lib/api";
import { errorMessageKey } from "@/lib/errors";
import {
  FIELDS,
  SECTIONS,
  initialValues,
  isVisible,
  serverErrors,
  toPatch,
  validate,
  type FieldName,
  type FieldSpec,
  type FormValues,
  type Validation,
} from "@/lib/form";
import { useI18n } from "@/lib/i18n/provider";
import type { MessageKey } from "@/lib/i18n/translate";
import type { CaseView } from "@/lib/types";
import { cn } from "@/lib/utils";

const NO_ERRORS: Validation = { fields: {}, form: [] };

/** Step 3 (task 4.4): the worker checks what the Intake read and fills in what is missing. */
export function ConfirmForm({ view, onConfirmed }: { view: CaseView; onConfirmed: (view: CaseView) => void }) {
  const { t } = useI18n();
  const [{ values: initial, prefilled }] = useState(() => initialValues(view));
  const [values, setValues] = useState<FormValues>(initial);
  const [touched, setTouched] = useState<Set<FieldName>>(new Set());
  const [errors, setErrors] = useState<Validation>(NO_ERRORS);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<MessageKey | null>(null);
  const missing = new Set(view.missing_fields);

  function change(name: FieldName, value: string) {
    setValues((v) => ({ ...v, [name]: value }));
    setTouched((s) => new Set(s).add(name));
    setErrors((e) => {
      const fields = { ...e.fields };
      delete fields[name];
      return { ...e, fields };
    });
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (busy) return;
    const checked = validate(values);
    setErrors(checked);
    setFailure(null);
    if (checked.form.length) {
      focusFirstError(checked);
      return;
    }
    setBusy(true);
    try {
      onConfirmed(await confirmCase(view.id, toPatch(values)));
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        const mapped = serverErrors(err.detail);
        setErrors(mapped);
        focusFirstError(mapped);
      } else {
        setFailure(errorMessageKey(err));
      }
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold">{t("confirm.title")}</h1>
        <p className="text-muted-foreground">{t("confirm.help")}</p>
        {view.status === "need_info" && (
          <p role="status" className="rounded-md bg-warning-bg px-3 py-2 text-sm text-warning-fg">
            {t("confirm.needInfo")}
          </p>
        )}
      </div>

      {SECTIONS.map((section) => {
        const fields = FIELDS.filter((f) => f.section === section.id && isVisible(f, values));
        return (
          <fieldset key={section.id} className="flex flex-col gap-4">
            <legend className="mb-2 text-lg font-medium">{t(section.label)}</legend>
            {fields.map((field) => (
              <FieldRow
                key={field.name}
                field={field}
                value={values[field.name]}
                onChange={(v) => change(field.name, v)}
                error={errors.fields[field.name]}
                confirm={prefilled.has(field.name) && !touched.has(field.name)}
                missing={missing.has(field.name) && !values[field.name]}
                disabled={busy}
              />
            ))}
          </fieldset>
        );
      })}

      {(errors.form.length > 0 || failure) && (
        <div role="alert" className="flex flex-col gap-1 text-sm text-destructive">
          {errors.form.map((key) => (
            <p key={key}>{t(key)}</p>
          ))}
          {failure && <p>{t(failure)}</p>}
        </div>
      )}

      <Button type="submit" size="lg" disabled={busy}>
        {busy ? t("confirm.submitting") : t("confirm.submit")}
      </Button>
    </form>
  );
}

function focusFirstError(v: Validation) {
  const first = FIELDS.find((f) => v.fields[f.name]);
  if (first) document.getElementById(`field-${first.name}`)?.focus();
}

function FieldRow({
  field,
  value,
  onChange,
  error,
  confirm,
  missing,
  disabled,
}: {
  field: FieldSpec;
  value: string;
  onChange: (value: string) => void;
  error: MessageKey | undefined;
  confirm: boolean;
  missing: boolean;
  disabled: boolean;
}) {
  const { t } = useI18n();
  const id = `field-${field.name}`;
  const describedBy = [field.help && `${id}-help`, error && `${id}-error`].filter(Boolean).join(" ") || undefined;
  const common = {
    id,
    name: field.name,
    disabled,
    "aria-invalid": error ? true : undefined,
    "aria-describedby": describedBy,
  };
  const optional = typeof field.empty === "object" || field.empty === "null";

  let control: React.ReactNode;
  if (field.kind === "select") {
    control = (
      <Select {...common} value={value} onChange={(e) => onChange(e.target.value)} required={!optional}>
        <option value="">{t("confirm.choose")}</option>
        {field.options?.map((option) => (
          <option key={option} value={option}>
            {t(`${field.optionPrefix}.${option}` as MessageKey)}
          </option>
        ))}
      </Select>
    );
  } else {
    const numeric = field.kind === "money" || field.kind === "decimal" || field.kind === "int";
    control = (
      <Input
        {...common}
        type={field.kind === "date" ? "date" : "text"}
        inputMode={field.kind === "int" ? "numeric" : numeric ? "decimal" : undefined}
        dir={numeric || field.kind === "date" ? "ltr" : undefined}
        autoComplete="off"
        value={value}
        placeholder={
          field.name === "unused_leave_days"
            ? t("confirm.dontKnow")
            : typeof field.empty === "object"
              ? String(field.empty.default)
              : undefined
        }
        onChange={(e) => onChange(e.target.value)}
        required={!optional}
      />
    );
  }

  return (
    <div
      className={cn(
        "flex flex-col gap-1.5 rounded-md",
        (missing || confirm) && "border-s-4 ps-3",
        missing ? "border-warning-fg" : confirm && "border-primary/30",
      )}
      data-missing={missing || undefined}
      data-confirm={confirm || undefined}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-x-2">
        <Label htmlFor={id}>{t(field.label)}</Label>
        {confirm && <span className="text-xs text-muted-foreground">{t("confirm.pleaseConfirm")}</span>}
      </div>
      {control}
      {field.help && (
        <p id={`${id}-help`} className="text-xs text-muted-foreground">
          {t(field.help)}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="text-sm text-destructive">
          {t(error)}
        </p>
      )}
    </div>
  );
}
