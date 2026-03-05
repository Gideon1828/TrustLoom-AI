import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";

export const generatePDF = (
  data,
  candidateName = "Candidate",
  resumeFile = null,
) => {
  const doc = new jsPDF();

  // Extract data
  const trustScore = data.final_trust_score || data.trust_score || 0;
  const riskLevel = data.risk_level || "UNKNOWN";
  const recommendation = data.recommendation || "N/A";
  const scoreBreakdown = data.score_breakdown || {};
  const flagsData = data.flags || {};
  const flags = flagsData.observations || [];
  const flagCount = flagsData.total_count || 0;

  // Extract scores
  const bertScore = scoreBreakdown.resume_quality?.score || 0;
  const lstmScore = scoreBreakdown.project_realism?.score || 0;
  const heuristicScore = scoreBreakdown.profile_validation?.score || 0;
  const resumeScore = bertScore + lstmScore;

  // Metadata
  const evaluationDate = new Date().toLocaleString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  const fileName = resumeFile ? resumeFile.name : "resume.pdf";

  // Colors
  const primaryColor = [59, 130, 246]; // Blue
  const secondaryColor = [107, 114, 128]; // Gray
  const successColor = [16, 185, 129]; // Green
  const warningColor = [245, 158, 11]; // Orange
  const dangerColor = [239, 68, 68]; // Red

  const riskColorMap = {
    LOW: successColor,
    MEDIUM: warningColor,
    HIGH: dangerColor,
  };

  const riskColor = riskColorMap[riskLevel] || warningColor;

  // Page width
  const pageWidth = doc.internal.pageSize.getWidth();

  // === HEADER ===
  doc.setFillColor(...primaryColor);
  doc.rect(0, 0, pageWidth, 40, "F");

  doc.setTextColor(255, 255, 255);
  doc.setFontSize(22);
  doc.setFont("helvetica", "bold");
  doc.text("Freelancer Trust Evaluation Report", pageWidth / 2, 18, {
    align: "center",
  });

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  doc.text("AI-Powered Trust Assessment System", pageWidth / 2, 28, {
    align: "center",
  });

  // === METADATA SECTION ===
  let yPos = 50;
  doc.setTextColor(0, 0, 0);
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.text("Evaluation Metadata", 14, yPos);

  yPos += 8;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(...secondaryColor);

  const metadata = [
    ["Candidate Name:", candidateName],
    ["Resume File:", fileName],
    ["Evaluation Date:", evaluationDate],
    ["Report Generated:", new Date().toLocaleString()],
  ];

  metadata.forEach(([label, value]) => {
    doc.setFont("helvetica", "bold");
    doc.text(label, 14, yPos);
    doc.setFont("helvetica", "normal");
    doc.text(value, 60, yPos);
    yPos += 6;
  });

  // === TRUST SCORE SECTION ===
  yPos += 8;
  doc.setFillColor(240, 240, 240);
  doc.roundedRect(14, yPos, pageWidth - 28, 40, 3, 3, "F");

  yPos += 12;
  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(...primaryColor);
  doc.text("Trust Score", pageWidth / 2, yPos, { align: "center" });

  yPos += 12;
  doc.setFontSize(24);
  const scoreColor =
    trustScore >= 80
      ? successColor
      : trustScore >= 55
        ? warningColor
        : dangerColor;
  doc.setTextColor(...scoreColor);
  doc.text(`${trustScore.toFixed(2)} / 100`, pageWidth / 2, yPos, {
    align: "center",
  });

  yPos += 10;
  doc.setFontSize(10);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(...riskColor);
  doc.text(`Risk Level: ${riskLevel}`, pageWidth / 2, yPos, {
    align: "center",
  });

  // === RECOMMENDATION ===
  yPos += 15;
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(0, 0, 0);
  doc.text("Recommendation", 14, yPos);

  yPos += 8;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(...secondaryColor);

  const recommendationText =
    recommendation === "TRUSTWORTHY"
      ? "This freelancer shows strong indicators of trustworthiness. Their profile demonstrates high credibility and low risk factors."
      : recommendation === "MODERATE"
        ? "This freelancer shows moderate trustworthiness. Consider reviewing specific flags and conducting additional verification before engagement."
        : recommendation === "RISKY"
          ? "This freelancer shows significant risk factors. Careful consideration and thorough verification are strongly recommended before any engagement."
          : recommendation;

  const splitText = doc.splitTextToSize(recommendationText, pageWidth - 28);
  doc.text(splitText, 14, yPos);
  yPos += splitText.length * 6;

  // === SCORE BREAKDOWN TABLE ===
  yPos += 10;
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(0, 0, 0);
  doc.text("Score Breakdown", 14, yPos);

  yPos += 5;

  autoTable(doc, {
    startY: yPos,
    head: [["Component", "Score", "Max", "Percentage"]],
    body: [
      [
        "Language Quality (BERT)",
        bertScore.toFixed(2),
        "25.00",
        `${((bertScore / 25) * 100).toFixed(1)}%`,
      ],
      [
        "Project Realism (LSTM)",
        lstmScore.toFixed(2),
        "45.00",
        `${((lstmScore / 45) * 100).toFixed(1)}%`,
      ],
      [
        "Profile Validation (Heuristic)",
        heuristicScore.toFixed(2),
        "30.00",
        `${((heuristicScore / 30) * 100).toFixed(1)}%`,
      ],
    ],
    theme: "striped",
    headStyles: { fillColor: primaryColor, fontSize: 9 },
    bodyStyles: { fontSize: 9 },
    margin: { left: 14, right: 14 },
  });

  yPos = doc.lastAutoTable.finalY + 10;

  // === SUMMARY TABLE ===
  autoTable(doc, {
    startY: yPos,
    head: [["Category", "Score", "Max"]],
    body: [
      ["Resume Quality (BERT + LSTM)", resumeScore.toFixed(2), "70.00"],
      ["Profile Validation (Heuristic)", heuristicScore.toFixed(2), "30.00"],
      ["Final Trust Score", trustScore.toFixed(2), "100.00"],
    ],
    theme: "plain",
    headStyles: {
      fillColor: [240, 240, 240],
      textColor: [0, 0, 0],
      fontSize: 9,
      fontStyle: "bold",
    },
    bodyStyles: { fontSize: 9 },
    foot: [
      [
        {
          content: `Overall Trust Score: ${trustScore.toFixed(2)} / 100`,
          colSpan: 3,
          styles: {
            halign: "center",
            fillColor: riskColor,
            textColor: [255, 255, 255],
            fontStyle: "bold",
          },
        },
      ],
    ],
    margin: { left: 14, right: 14 },
  });

  yPos = doc.lastAutoTable.finalY + 15;

  // === FLAGS SECTION ===
  if (flags.length > 0) {
    // Check if we need a new page
    if (yPos > 240) {
      doc.addPage();
      yPos = 20;
    }

    doc.setFontSize(11);
    doc.setFont("helvetica", "bold");
    doc.setTextColor(0, 0, 0);
    doc.text(`Observations & Flags (${flagCount})`, 14, yPos);

    yPos += 5;

    const flagRows = flags.map((flag, index) => {
      const flagMessage = flag.message || flag;
      const flagSource = flag.source || "";
      const flagText = flagSource
        ? `${flagMessage} (${flagSource})`
        : flagMessage;
      return [`${index + 1}.`, flagText];
    });

    autoTable(doc, {
      startY: yPos,
      head: [["#", "Observation"]],
      body: flagRows,
      theme: "striped",
      headStyles: { fillColor: [245, 158, 11], fontSize: 9 },
      bodyStyles: { fontSize: 8 },
      columnStyles: {
        0: { cellWidth: 10 },
        1: { cellWidth: "auto" },
      },
      margin: { left: 14, right: 14 },
    });
  }

  // === FOOTER ===
  const pageCount = doc.internal.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(...secondaryColor);
    doc.setFont("helvetica", "normal");

    const footerY = doc.internal.pageSize.getHeight() - 10;
    doc.text("Freelancer Trust Evaluation System © 2026", 14, footerY);
    doc.text(`Page ${i} of ${pageCount}`, pageWidth - 14, footerY, {
      align: "right",
    });

    // Add thin line above footer
    doc.setDrawColor(...secondaryColor);
    doc.setLineWidth(0.5);
    doc.line(14, footerY - 5, pageWidth - 14, footerY - 5);
  }

  // Save the PDF
  const pdfFileName = `Freelancer_Trust_Report_${candidateName.replace(/\s+/g, "_")}_${new Date().toISOString().split("T")[0]}.pdf`;
  doc.save(pdfFileName);
};
