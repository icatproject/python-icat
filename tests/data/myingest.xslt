<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
		xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:output method="xml"/>

    <xsl:template match="/myingest">
	<icatdata>
	    <xsl:apply-templates/>
	</icatdata>
    </xsl:template>

    <xsl:template match="/myingest/_environment"/>

    <xsl:template match="/myingest/head"/>

    <xsl:template match="/myingest/data">
	<data>
	    <xsl:apply-templates/>
	</data>
    </xsl:template>

    <xsl:template match="/myingest/data/dataset">
	<dataset>
	    <xsl:copy-of select="@id"/>
	    <complete>false</complete>
	    <xsl:apply-templates select="description"/>
	    <xsl:copy-of select="endDate"/>
	    <xsl:copy-of select="name"/>
	    <xsl:copy-of select="startDate"/>
	    <investigation ref="_Investigation"/>
	    <xsl:apply-templates select="sample"/>
	    <type name="raw"/>
	    <xsl:copy-of select="datasetInstruments"/>
	    <xsl:copy-of select="datasetTechniques"/>
	    <parameters>
		<stringValue>x-ray</stringValue>
		<type name="Probe"/>
	    </parameters>
	    <xsl:copy-of select="parameters"/>
	</dataset>
    </xsl:template>

    <xsl:template match="/myingest/data/dataset/description">
	<xsl:copy>
	    <xsl:value-of select="concat('My Ingest: ', .)"/>
	</xsl:copy>
    </xsl:template>

    <xsl:template match="/myingest/data/dataset/sample">
	<xsl:copy>
	    <xsl:attribute name="investigation.ref">_Investigation</xsl:attribute>
	    <xsl:copy-of select="@*"/>
	</xsl:copy>
    </xsl:template>

    <xsl:template match="*">
	<xsl:copy-of select="."/>
    </xsl:template>

</xsl:stylesheet>
