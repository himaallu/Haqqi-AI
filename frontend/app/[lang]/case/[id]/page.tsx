import { CaseFlow } from "@/components/case-flow";

export default async function CasePage({ params }: PageProps<"/[lang]/case/[id]">) {
  const { id } = await params;
  return <CaseFlow caseId={id} />;
}
