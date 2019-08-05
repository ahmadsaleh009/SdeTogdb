"""
8-5-2019

Ahmad Saleh 


A generic tool to convert multiple mdf files to gdb
https://community.esri.com/thread/193090-a-generic-tool-to-convert-multiple-mdf-files-to-gdb

"""


import urllib, urllib2, json
import arcpy
import sys, os



class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "SDE TO GDB Toolbox"
        self.alias = "SDETOGDBToolbox"

        # List of tool classes associated with this toolbox
        self.tools = [SDETOGDB]


class SDETOGDB(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "sde to gdb with Server on/off "
        self.description = "copy the content of the sde to gdb"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        # First parameter
        param0 = arcpy.Parameter(
            displayName="ArcGIS server Full Machine Name",
            name="server",
            datatype="GPType",
            parameterType="Required",
            direction="Input")
        param0.value = "Server1.domain.local"

        # Second parameter
        param1 = arcpy.Parameter(
            displayName="Port",
            name="port",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param1.value = "6080"

        # Third parameter
        param2 = arcpy.Parameter(
            displayName="ArcGIS Server User",
            name="adminUser",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        # Fourth parameter
        param3 = arcpy.Parameter(
            displayName="ArcGIS Server Password",
            name="adminPass",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        # 5th parameter
        param4 = arcpy.Parameter(
            displayName="SDE Connection Folder",
            name="inFolder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        
        # 6th parameter
        param5 = arcpy.Parameter(
            displayName="GDB Destination Folder",
            name="outFolder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        
        

        params = [param0, param1, param2,param3,param4,param5]

        return params

    

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        server = parameters[0].valueAsText
        port = parameters[1].valueAsText
        adminUser = parameters[2].valueAsText
        adminPass = parameters[3].valueAsText
        inFolder=parameters[4].valueAsText
        outFolder=parameters[5].valueAsText

        def gentoken(server, port, adminUser, adminPass, expiration=60):
                #Re-usable function to get a token required for Admin changes

                query_dict = {'username':   adminUser,
                                'password':   adminPass,
                                'expiration': str(expiration),
                                'client':     'requestip'}

                query_string = urllib.urlencode(query_dict)
                url = "http://{}:{}/arcgis/admin/generateToken".format(server, port)

                token = json.loads(urllib.urlopen(url + "?f=json", query_string).read())

                if "token" not in token:
                        arcpy.AddError(token['messages'])
                        quit()
                else:
                        return token['token']

        def StopStartServer(server, port, adminUser, adminPass,operation,token=None):

            ''' Function to Start / Stop ArcGIS server.
            Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).


            If a token exists, you can pass one in for use.


            '''

            if token is None:
                token = gentoken(server, port, adminUser, adminPass)

            adminURL="http://{}:{}/arcgis/admin/machines/{}/{}/?f=pjson&token={}".format(server, port,server,operation,token)
            status=urllib2.urlopen(adminURL," ").read()

            if 'success' in status:
                    arcpy.AddMessage("ArcGIS Server ===>  "+ operation)
            else:
                    arcpy.AddWarning(status)

            return



        def dbCopy(inFolder,outFolder):
            ''' Function to Copy the content of sde connections stored in a folder to gdb.
            the function will delete all gdb files stored in the destination folder

            '''





            arcpy.AddMessage("Running SDE to GDB Tool...")
            arcpy.env.workspace=inFolder
            arcpy.env.overwriteOutput=True

            Workspace=arcpy.ListWorkspaces("*","SDE")

            #Collect all sde file names in a list then delete all gdb that maches the list
            gdb_delete=[]
            for sde in Workspace:
                sde_name=os.path.basename(sde)
                gdb_name=sde_name.replace(".sde",".gdb")
                gdb_delete.append(str(gdb_name))
                arcpy.AddMessage(str(gdb_name)+" will be deleted ...")





            #Delete all existing gdb files from the folder
            arcpy.AddMessage("Deleting old gdb Files ...")
            for the_file in os.listdir(outFolder):
                file_path = os.path.join(outFolder, the_file)

                if the_file in gdb_delete:

                    try:
                            arcpy.Compact_management(file_path)
                            arcpy.Delete_management(file_path)
                            arcpy.AddMessage(str(file_path) + " Was Deleted")

                    except Exception as e:
                        arcpy.AddWarning(e)




            for DBConn in Workspace:
                arcpy.env.workspace=DBConn

                GDBfileName=os.path.basename(DBConn)
                arcpy.AddMessage( "Working on: "+str(GDBfileName))
                arcpy.AddMessage("...\n")
                arcpy.CreateFileGDB_management(outFolder, GDBfileName)
                GDBCreationMSG= GDBfileName +" Was Created at the following Location " + outFolder +"\n"
                arcpy.AddMessage(str(GDBCreationMSG))
                arcpy.AddMessage("...\n")
                SDEfcList=arcpy.ListFeatureClasses()
                SDEtableList=arcpy.ListTables()
                SDEDatasetesList=arcpy.ListDatasets("","Feature")

                try:

                    GDBfileNameGDB=GDBfileName.replace(".sde",".gdb")



                    GDBPath=outFolder+"/"+GDBfileNameGDB
                    arcpy.AddMessage("...\n")

                    arcpy.AddMessage("Number of Feature classes:  "+str(len(SDEfcList)))
                    for dataitem in SDEfcList:
                        arcpy.CopyFeatures_management(dataitem, os.path.join(GDBPath,dataitem.split("SDE.")[0]))
                        arcpy.AddMessage(str(dataitem) + "   was copied")

                    arcpy.AddMessage( "All Feature classes  inside the database were copied.\n")
                    arcpy.AddMessage("DONE\n")
                    arcpy.AddMessage("...\n")


                except:
                    arcpy.AddWarning("Failed to copy Feature Classes .\n")



                try:
                    arcpy.AddMessage("Number of Tables:  "+str(len(SDEtableList)))

                    for tableitem in SDEtableList:
                        arcpy.TableToGeodatabase_conversion(tableitem,GDBPath)
                        arcpy.AddMessage(str(tableitem) + "   was copied\n")

                    arcpy.AddMessage("All Tables  inside the database were copied.\n")
                    arcpy.AddMessage("DONE\n")
                    arcpy.AddMessage( "...\n")


                except:
                    arcpy.AddWarning("Failed to  copy Tables.\n")



                try:
                    arcpy.AddMessage("Number of Datasets:  "+str(len(SDEDatasetesList)))
                    for ds in SDEDatasetesList :
                        dsnm=ds.split(".")
                        dsName=dsnm[-1]
                        arcpy.Copy_management(ds, os.path.join(GDBPath,dsName), data_type="FeatureDataset")
                        arcpy.AddMessage( str(ds) + "   was copied")

                except:
                    arcpy.AddWarning( "Failed to copy Feature Datasets .\n")

                arcpy.AddMessage("All Datasets  inside the database were copied.\n")
                arcpy.AddMessage( "DONE\n")
                arcpy.AddMessage("...\n")

            arcpy.AddMessage( "...\n")
            arcpy.AddMessage( "Finished Copying the Data...\n")
            return





        StopStartServer(server, port, adminUser, adminPass,operation="stop")
        dbCopy(inFolder,outFolder)
        StopStartServer(server, port, adminUser, adminPass,operation="start")


        return
