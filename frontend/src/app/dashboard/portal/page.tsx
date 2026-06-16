"use client";

import { StaffLayout, useStaffAuth } from "@/components/StaffLayout";
import { StaffPage } from "@/components/StaffPage";
import { PortalCorpo } from "@/components/PortalCorpo";

export default function DashboardPortalPage() {
  const { usuario, ready, sair } = useStaffAuth();

  return (
    <StaffLayout loading={!ready}>
      {usuario && (
        <StaffPage
          title="Portal dos Pais"
          description="Visualize o portal como as famílias enxergam."
          onLogout={sair}
        >
          <PortalCorpo usuario={usuario} modoPreview />
        </StaffPage>
      )}
    </StaffLayout>
  );
}
