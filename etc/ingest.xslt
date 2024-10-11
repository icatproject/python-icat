<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" 
		xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:output method="xml"/>

    <xsl:variable name="samp_inv_ref">
	<xsl:choose>
	    <xsl:when test="/icatingest/_environment/@sample_investigation_relation = 'one'">
		<xsl:text>investigation.ref</xsl:text>
	    </xsl:when>
	    <xsl:when test="/icatingest/_environment/@sample_investigation_relation = 'many'">
		<xsl:text>investigationSamples.investigation.ref</xsl:text>
	    </xsl:when>
	    <xsl:otherwise>
		<xsl:message terminate="yes">
		    ERROR: invalid environment
		</xsl:message>
	    </xsl:otherwise>
	</xsl:choose>
    </xsl:variable>

    <xsl:template match="/icatingest">
	<icatdata>
	    <xsl:apply-templates/>
	</icatdata>
    </xsl:template>

    <xsl:template match="/icatingest/_environment"/>

    <xsl:template match="/icatingest/head"/>

    <xsl:template match="/icatingest/data">
	<data>
	    <xsl:apply-templates/>
	</data>
    </xsl:template>

    <xsl:template match="/icatingest/data/dataset">
	<dataset>
	    <xsl:copy-of select="@id"/>
	    <xsl:element name="complete">
		<xsl:value-of
		    select="/icatingest/_environment/@dataset_complete"/>
	    </xsl:element>
	    <xsl:copy-of select="description"/>
	    <xsl:copy-of select="endDate"/>
	    <xsl:copy-of select="name"/>
	    <xsl:copy-of select="startDate"/>
	    <investigation ref="_Investigation"/>
	    <xsl:apply-templates select="sample"/>
	    <xsl:element name="type">
		<xsl:attribute name="name">
		    <xsl:value-of
			select="/icatingest/_environment/@datasettype_name"/>
		</xsl:attribute>
	    </xsl:element>
	    <xsl:copy-of select="datasetInstruments"/>
	    <xsl:copy-of select="datasetTechniques"/>
	    <xsl:copy-of select="parameters"/>
	</dataset>
    </xsl:template>

    <xsl:template match="/icatingest/data/dataset/sample">
	<xsl:copy>
	    <xsl:attribute name="{$samp_inv_ref}">_Investigation</xsl:attribute>
	    <xsl:copy-of select="@*"/>
	</xsl:copy>
    </xsl:template>

    <xsl:template match="*">
	<xsl:copy-of select="."/>
    </xsl:template>

</xsl:stylesheet>
