<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
		xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:output method="xml"/>

    <xsl:template match="/icatingest">
	<icatdata>
	    <xsl:apply-templates/>
	</icatdata>
    </xsl:template>

    <xsl:template match="/icatingest/_environment"/>

    <xsl:template match="/icatingest/head">
	<head>
	    <date>2024-01-22T14:30:51+01:00</date>
	    <apiversion>
		<xsl:copy-of select="string(/icatingest/_environment/@icat_version)"/>
	    </apiversion>
	    <generator>
		<xsl:copy-of select="string(/icatingest/_environment/@generator)"/>
	    </generator>
	</head>
    </xsl:template>

    <xsl:template match="/icatingest/data">
	<data>
	    <xsl:apply-templates/>
	</data>
    </xsl:template>

    <xsl:template match="/icatingest/data/dataset">
	<dataset>
	    <xsl:copy-of select="@id"/>
	    <complete>false</complete>
	    <xsl:copy-of select="description"/>
	    <xsl:copy-of select="endDate"/>
	    <xsl:copy-of select="name"/>
	    <xsl:copy-of select="startDate"/>
	    <investigation ref="_Investigation"/>
	    <xsl:apply-templates select="sample"/>
	    <type name="raw"/>
	    <xsl:copy-of select="datasetInstruments"/>
	    <xsl:copy-of select="datasetTechniques"/>
	    <xsl:copy-of select="parameters"/>
	</dataset>
    </xsl:template>

    <xsl:template match="/icatingest/data/dataset/sample">
	<xsl:copy>
	    <xsl:attribute name="investigation.ref">_Investigation</xsl:attribute>
	    <xsl:copy-of select="@*"/>
	</xsl:copy>
    </xsl:template>

    <xsl:template match="*">
	<xsl:copy-of select="."/>
    </xsl:template>

</xsl:stylesheet>
