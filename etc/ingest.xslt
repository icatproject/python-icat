<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" 
		xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:output method="xml"/>

    <xsl:template match="/icatingest">
	<icatdata>
	    <xsl:apply-templates/>
	</icatdata>
    </xsl:template>

    <xsl:template match="/icatingest/head"/>

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
	    <type name="raw"/>
	    <xsl:for-each select="datasetInstruments">
		<xsl:copy-of select="."/>
	    </xsl:for-each>
	    <xsl:for-each select="datasetTechniques">
		<xsl:copy-of select="."/>
	    </xsl:for-each>
	    <xsl:for-each select="parameters">
		<xsl:copy-of select="."/>
	    </xsl:for-each>
	</dataset>
    </xsl:template>

    <xsl:template match="*">
	<xsl:copy-of select="."/>
    </xsl:template>

</xsl:stylesheet>
