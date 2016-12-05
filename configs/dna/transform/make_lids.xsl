<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

 <!--   <xsl:import href="../../../xslt/linked-data-api.xsl"/>
-->

    <xsl:output method="html" omit-xml-declaration="yes" doctype-public="-//W3C//DTD HTML 4.01//EN"
        version="4.01" encoding="utf-8" indent="yes"/>

    <!-- variable bindings are passed by ELDA as stylesheet parameter bindings -->
    <xsl:param name="objectid"/>
		
    <xsl:param name="_resourceRoot">/</xsl:param>
    <xsl:param name="activeImageBase" select="concat($_resourceRoot,'images/green/16x16')"/>
    <xsl:param name="inactiveImageBase" select="concat($_resourceRoot,'images/grey/16x16')"/>

    <xsl:param name="title"/>

    <xsl:param name="serviceTitle">Test Title</xsl:param>
    <xsl:param name="serviceAuthor">Test Author</xsl:param>
    <xsl:param name="serviceAuthorEmail">test.author@csiro.au</xsl:param>
    <xsl:param name="serviceHomePage">http://test.homepage/here</xsl:param>

    <xsl:param name="SISSDefaultResourceDirBase"/>

    <xsl:param name="myResourceDirBase">/</xsl:param>
    <xsl:param name="myResourceCSSBase" select="concat($myResourceDirBase, 'css/')"/>
    <xsl:param name="myResourceImagesBase" select="concat($myResourceDirBase, 'images/')"/>
    <xsl:param name="myResourceJsBase" select="concat($myResourceDirBase, 'js/')"/>
    <xsl:param name="myResourceCSSResultFile" select="concat($myResourceCSSBase, 'mystyle.css')"/>

    <xsl:param name="graphColour" select="'#577D00'"/>


    <xsl:variable name="idroot" select="/result/primaryTopic/@href"/>
    <xsl:variable name="id" select="$idroot"/>

    <xsl:key name="formats" match="hasFormat/item" use="@href"/>
    <xsl:key name="format_single" match="hasFormat" use="@href"/>

    <xsl:output method="html" indent="yes"/>

    <xsl:template match="result">
        <html>
            <head>
                <xsl:apply-templates select="." mode="title"/>
                <xsl:apply-templates select="." mode="meta"/>
                <xsl:apply-templates select="." mode="style"/>
            </head>
            <body>
                <div id="page">
                   <xsl:apply-templates select="." mode="header"/>
                    <xsl:apply-templates select="primaryTopic"/>
<!--                    <xsl:apply-templates select="." mode="footer"/>-->
                </div>
            </body>
        </html>
    </xsl:template>

    <xsl:template match="result" mode="header">
        <nav class="site">
    
        <header>
            <h1>      
                <xsl:variable name="label" select="primaryTopic/label"/>
                <xsl:value-of select="$label"/></h1>
        </header>
        </nav>
    </xsl:template>
    
    <xsl:template match="result" mode="title">
        <title>
            <xsl:choose>
                <xsl:when test="$title != ''"><xsl:value-of select="$title" /></xsl:when>
                <xsl:otherwise>Linked Data - alternate resource list</xsl:otherwise>
            </xsl:choose>
        </title>
    </xsl:template>
    
    <xsl:template match="result" mode="meta">
        <link rel="shortcut icon" href="{$myResourceImagesBase}/lid.png" type="image/x-icon" /> 

    </xsl:template>
    
    <xsl:template match="result" mode="style">
        <link rel="stylesheet" href="{$_resourceRoot}css/html5reset-1.6.1.css" type="text/css"/>
        <link rel="stylesheet" href="{$_resourceRoot}css/jquery-ui.css" type="text/css"/>
        <link rel="stylesheet" href="{$_resourceRoot}css/smoothness/jquery-ui.css" type="text/css"/>
        <link rel="stylesheet" href="{$_resourceRoot}css/result.css" type="text/css"/>
        <link rel="stylesheet" href="{$myResourceCSSResultFile}" type="text/css"/>
        <xsl:comment>
		<xsl:text>[if lt IE 9]&gt;</xsl:text>
		<xsl:text>&lt;link rel="stylesheet" href="</xsl:text><xsl:value-of select="$_resourceRoot"/><xsl:text>css/ie.css" type="text/css">&lt;/link></xsl:text>
		<xsl:text>&lt;![endif]</xsl:text>
	</xsl:comment>
    </xsl:template>

    <xsl:template match="result/primaryTopic">
 
        
        <H1></H1>
        <xsl:choose>
            <xsl:when test="$objectid = '' or $objectid = 'None' ">
                <H1>Information resources available for <a href="{$id}" target="_blank"
            title="Go to default view of object"><xsl:value-of select="$id"/></a></H1>
            
                <xsl:apply-templates select="void_feature|feature">
                        <xsl:with-param name="id"><xsl:value-of select="$id"/>
                        </xsl:with-param>
                        <xsl:with-param name="scope">set</xsl:with-param>
                    </xsl:apply-templates>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="id" select="concat($idroot, '/', $objectid)"/>
                <H1> Information resources available for specified
                    object: <a href="{$id}"  target="_blank"
            title="Go to default view of object"><xsl:value-of select="$id"/></a></H1>
                <xsl:apply-templates select="void_feature|feature">
                    <xsl:with-param name="id"><xsl:value-of select="$id"/></xsl:with-param>
                    <xsl:with-param name="scope">item</xsl:with-param>
                </xsl:apply-templates>
                <H1>Dataset related links: <a href="{$idroot}"  target="_blank"
            title="Go to default view of dataset information"><xsl:value-of select="$idroot"/></a></H1>
                <xsl:apply-templates select="void_feature|feature">
                    <xsl:with-param name="id"><xsl:value-of select="$idroot"/></xsl:with-param>
                    <xsl:with-param name="scope">set</xsl:with-param>
                </xsl:apply-templates>
            </xsl:otherwise>
        </xsl:choose>


    </xsl:template>

    <xsl:template match="void_feature|feature">
        <xsl:param name="scope">set</xsl:param>
        <xsl:param name="id"/>
        <TABLE BORDER="1">
            <TR>
                <TH>View</TH>
                <TH>Description</TH>
                <TH>Resources</TH>
            </TR>
            <xsl:apply-templates select="item" mode="views">
                <xsl:with-param name="scope" select="$scope"/>
                <xsl:with-param name="id">
                    <xsl:value-of select="$id"/>
                </xsl:with-param>
            </xsl:apply-templates>
        </TABLE>
    </xsl:template>

    <xsl:template match="item" mode="views">
        <xsl:param name="scope">set</xsl:param>
        <xsl:param name="id"/>
        <xsl:variable name="view" select="lid_viewName|viewName"/>
        <xsl:variable name="vt" select="viewType/@href|lid_viewType/@href"/>
        
        <xsl:if test="(count(lid_featurescope) + count(featurescope) = 0 ) or featurescope = $scope or lid_featurescope = $scope">

            <TR>
                <TD>
                    <xsl:choose>
                        <xsl:when test="count(lid_viewType) + count(viewType) = 1" >
                            <a href="{$vt}"  target="_blank"
            title="{$vt}">
                                <xsl:value-of select="$view"/>
                            </a>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$view"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </TD>
                <TD>
                    <xsl:value-of select="label"/>
                </TD>
                <TD>
                    <xsl:apply-templates select="hasFormat">
                        <xsl:with-param name="view">
                            <xsl:value-of select="$view"/>
                        </xsl:with-param>
                        <xsl:with-param name="id">
                            <xsl:value-of select="$id"/>
                        </xsl:with-param>
                    </xsl:apply-templates>
                    <xsl:if test="$view='SPARQL'">
                        <xsl:call-template name="se"/>
                    </xsl:if>
                </TD>
            </TR>
        </xsl:if>
    </xsl:template>

    <xsl:template match="hasFormat">
        <xsl:param name="view"/>
        <xsl:param name="id"/>
        <!--      <xsl:variable name="format" select="lid_ldatoken"/>-->
        <!-- two cases to handle - if a single value or or if multiple values embedded in "item" list .... why o why o why not just be consistent 
        and have single item lists? -->
        <xsl:if test="@href">
            <xsl:call-template name="format">
                <xsl:with-param name="view">
                    <xsl:value-of select="$view"/>
                </xsl:with-param>
                <xsl:with-param name="id">
                    <xsl:value-of select="$id"/>
                </xsl:with-param>
                <xsl:with-param name="format">
                    <xsl:value-of select="key('format_single', @href)/lid_ldatoken"/>
                    <xsl:value-of select="key('format_single', @href)/ldatoken"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>
        <xsl:apply-templates select="item" mode="formats">
            <xsl:with-param name="view">
                <xsl:value-of select="$view"/>
            </xsl:with-param>
            <xsl:with-param name="id">
                <xsl:value-of select="$id"/>
            </xsl:with-param>
        </xsl:apply-templates>
    </xsl:template>

    <xsl:template match="item" mode="formats">
        <xsl:param name="view"/>
        <xsl:param name="id"/>
        <xsl:call-template name="format">
            <xsl:with-param name="view">
                <xsl:value-of select="$view"/>
            </xsl:with-param>
            <xsl:with-param name="id">
                <xsl:value-of select="$id"/>
            </xsl:with-param>
            <xsl:with-param name="format">
                <xsl:value-of select="key('formats', @href)/lid_ldatoken"/>
                <xsl:value-of select="key('formats', @href)/ldatoken"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>


    <xsl:template name="format">
        <xsl:param name="view"/>
        <xsl:param name="format"/>
        <xsl:param name="id"/>
        <!--      <xsl:variable name="format" select="lid_ldatoken"/>--> [<a
            href="{$id}?_view={$view}&amp;_format={$format}" target="_blank"
            title="{$id}?_view={$view}&amp;_format={$format}"><xsl:value-of select="$format"
            /></a>] </xsl:template>

    <xsl:template name="se">
        <xsl:variable name="sp" select="//void_sparqlendpoint/@href"/>

        <xsl:value-of select="$sp"/>

    </xsl:template>

</xsl:stylesheet>
